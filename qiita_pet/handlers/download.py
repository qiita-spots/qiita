# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from base64 import b64encode
from datetime import datetime, timedelta, timezone
from io import BytesIO
from os import walk
from os.path import basename, getctime, getsize, isdir, join
from tempfile import mkdtemp
from uuid import uuid4
from zipfile import ZipFile

from jose import jwt as jose_jwt
from tornado.gen import coroutine
from tornado.web import HTTPError, authenticated

from qiita_core.qiita_settings import qiita_config
from qiita_core.util import execute_as_transaction, get_release_info
from qiita_db.artifact import Artifact
from qiita_db.download_link import DownloadLink
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.meta_util import validate_filepath_access_by_user
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.study import Study
from qiita_db.user import User
from qiita_db.util import (
    filepath_id_to_object_id,
    filepath_id_to_rel_path,
    get_data_types,
    get_db_files_base_dir,
    get_filepath_information,
    get_mountpoint,
    get_work_base_dir,
    retrieve_filepaths,
)
from qiita_pet.handlers.api_proxy.util import check_access
from qiita_pet.handlers.artifact_handlers.base_handlers import check_artifact_access

from .base_handlers import BaseHandler


class BaseHandlerDownload(BaseHandler):
    def _check_permissions(self, sid):
        # Check general access to study
        study_info = check_access(sid, self.current_user.id)
        if study_info:
            raise HTTPError(
                405,
                reason="%s: %s, %s"
                % (study_info["message"], self.current_user.email, sid),
            )
        return Study(sid)

    def _finish_generate_files(self, filename, text):
        self.set_header("Content-Description", "text/csv")
        self.set_header("Expires", "0")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Content-Disposition", "attachment; filename=%s" % filename)
        self.write(text)
        self.finish()

    def _generate_files(self, header_name, accessions, filename):
        text = "sample_name\t%s\n%s" % (
            header_name,
            "\n".join(["%s\t%s" % (k, v) for k, v in accessions.items()]),
        )

        self._finish_generate_files(filename, text)

    def _list_dir_files_nginx(self, dirpath):
        """Generates a nginx list of files in the given dirpath for nginx

        Parameters
        ----------
        dirpath : str
            Path to the directory

        Returns
        -------
        list of (str, str, str)
            The path information needed by nginx for each file in the
            directory
        """
        basedir = get_db_files_base_dir()
        basedir_len = len(basedir) + 1
        to_download = []
        for dp, _, fps in walk(dirpath):
            for fn in fps:
                fullpath = join(dp, fn)
                spath = fullpath
                if fullpath.startswith(basedir):
                    spath = fullpath[basedir_len:]
                to_download.append((spath, spath, "-", str(getsize(fullpath))))
        return to_download

    def _list_artifact_files_nginx(self, artifact):
        """Generates a nginx list of files for the given artifact

        Parameters
        ----------
        artifact : qiita_db.artifact.Artifact
            The artifact to retrieve the files

        Returns
        -------
        list of (str, str, str)
            The path information needed by nginx for each file in the artifact
        """
        basedir = get_db_files_base_dir()
        basedir_len = len(basedir) + 1
        to_download = []
        for i, x in enumerate(artifact.filepaths):
            # ignore if tgz as they could create problems and the
            # raw data is in the folder
            if x["fp_type"] == "tgz":
                continue
            if isdir(x["fp"]):
                # If we have a directory, we actually need to list all the
                # files from the directory so NGINX can actually download all
                # of them
                to_download.extend(self._list_dir_files_nginx(x["fp"]))
            elif x["fp"].startswith(basedir):
                spath = x["fp"][basedir_len:]
                to_download.append((spath, spath, "-", str(x["fp_size"])))
            else:
                to_download.append((x["fp"], x["fp"], "-", str(x["fp_size"])))

        for pt in artifact.prep_templates:
            # the latest prep template file is always the first [0] tuple and
            # we need the filepath [1]
            pt_fp = pt.get_filepaths()
            if pt_fp:
                pt_fp = pt_fp[0][1]
                spt_fp = pt_fp
                if pt_fp.startswith(basedir):
                    spt_fp = pt_fp[basedir_len:]
                fname = "mapping_files/%s_mapping_file.txt" % artifact.id
                to_download.append((spt_fp, fname, "-", str(getsize(pt_fp))))
        return to_download

    def _write_nginx_file_list(self, to_download):
        """Writes out the nginx file list

        Parameters
        ----------
        to_download : list of (str, str, str, str)
            The file list information
        """
        all_files = "\n".join(
            [
                "%s %s /protected/%s %s" % (fp_checksum, fp_size, fp, fp_name)
                for fp, fp_name, fp_checksum, fp_size in to_download
            ]
        )

        self.set_header("X-Archive-Files", "zip")
        self.write("%s\n" % all_files)

    def _set_nginx_headers(self, fname):
        """Sets commong nginx headers

        Parameters
        ----------
        fname : str
            Nginx's output filename
        """
        self.set_header("Content-Description", "File Transfer")
        self.set_header("Expires", "0")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Content-Disposition", "attachment; filename=%s" % fname)

    def _write_nginx_placeholder_file(self, fp):
        """Writes nginx placeholder file in case that nginx is not set up

        Parameters
        ----------
        fp : str
            The path to be downloaded through nginx
        """
        # If we don't have nginx, write a file that indicates this
        self.write(
            "This installation of Qiita was not equipped with "
            "nginx, so it is incapable of serving files. The file "
            "you attempted to download is located at %s" % fp
        )


class DownloadHandler(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, filepath_id):
        fid = int(filepath_id)

        if not validate_filepath_access_by_user(self.current_user, fid):
            raise HTTPError(
                403,
                "%s doesn't have access to "
                "filepath_id: %s" % (self.current_user.email, str(fid)),
            )

        relpath = filepath_id_to_rel_path(fid)
        fp_info = get_filepath_information(fid)
        fname = basename(relpath)

        if fp_info["filepath_type"] in ("directory", "html_summary_dir"):
            # This is a directory, we need to list all the files so NGINX
            # can download all of them
            to_download = self._list_dir_files_nginx(fp_info["fullpath"])
            self._write_nginx_file_list(to_download)
            fname = "%s.zip" % fname
        else:
            self._write_nginx_placeholder_file(relpath)
            self.set_header("Content-Type", "application/octet-stream")
            self.set_header("Content-Transfer-Encoding", "binary")
            self.set_header("X-Accel-Redirect", "/protected/" + relpath)
            aid = filepath_id_to_object_id(fid)
            if aid is not None:
                fname = "%d_%s" % (aid, fname)

        self._set_nginx_headers(fname)
        self.finish()


class DownloadStudyBIOMSHandler(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, study_id):
        study_id = int(study_id)
        study = self._check_permissions(study_id)
        # loop over artifacts and retrieve those that we have access to
        to_download = []
        # The user has access to the study, but we don't know if the user
        # can do whatever he wants to the study or just access the public
        # data. (1) an admin has access to all the data; (2) if the study
        # is not public, and the user has access, then it has full access
        # to the data; (3) if the study is public and the user is not the owner
        # or the study is shared with him, then the user doesn't have full
        # access to the study data
        full_access = (
            (self.current_user.level == "admin")
            | (study.status != "public")
            | (
                (self.current_user == study.owner)
                | (self.current_user in study.shared_with)
            )
        )

        for a in study.artifacts(artifact_type="BIOM"):
            if full_access or (a.visibility == "public" and not a.has_human):
                to_download.extend(self._list_artifact_files_nginx(a))

        self._write_nginx_file_list(to_download)

        zip_fn = "study_%d_%s.zip" % (
            study_id,
            datetime.now().strftime("%m%d%y-%H%M%S"),
        )

        self._set_nginx_headers(zip_fn)
        self.finish()


class DownloadRelease(BaseHandlerDownload):
    @coroutine
    def get(self, extras):
        biom_metadata_release, archive_release = get_release_info()
        if extras == "archive":
            relpath = archive_release[1]
        else:
            relpath = biom_metadata_release[1]

        # If we don't have nginx, write a file that indicates this
        # Note that this configuration will automatically create and download
        # ("on the fly") the zip file via the contents in all_files
        self._write_nginx_placeholder_file(relpath)

        self._set_nginx_headers(basename(relpath))

        self.set_header("Content-Type", "application/octet-stream")
        self.set_header("Content-Transfer-Encoding", "binary")
        self.set_header("X-Accel-Redirect", f"/protected-working_dir/{relpath}")
        self.finish()


class DownloadRawData(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, study_id):
        study_id = int(study_id)
        study = self._check_permissions(study_id)
        user = self.current_user
        # Checking access options
        is_owner = study.has_access(user, True)
        public_raw_download = study.public_raw_download
        if not is_owner and not public_raw_download:
            raise HTTPError(
                405,
                reason="%s: %s, %s"
                % ("No raw data access", self.current_user.email, str(study_id)),
            )

        # loop over artifacts and retrieve raw data (no parents)
        to_download = []
        for a in study.artifacts():
            if not a.parents:
                if not is_owner and (a.visibility != "public" or a.has_human):
                    continue
                to_download.extend(self._list_artifact_files_nginx(a))

        self._write_nginx_file_list(to_download)

        zip_fn = "study_raw_data_%d_%s.zip" % (
            study_id,
            datetime.now().strftime("%m%d%y-%H%M%S"),
        )

        self._set_nginx_headers(zip_fn)
        self.finish()


class DownloadEBISampleAccessions(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, study_id):
        sid = int(study_id)
        self._check_permissions(sid)

        self._generate_files(
            "sample_accession",
            SampleTemplate(sid).ebi_sample_accessions,
            "ebi_sample_accessions_study_%s.tsv" % sid,
        )


class DownloadEBIPrepAccessions(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, prep_template_id):
        pid = int(prep_template_id)
        pt = PrepTemplate(pid)
        sid = pt.study_id

        self._check_permissions(sid)

        self._generate_files(
            "experiment_accession",
            pt.ebi_experiment_accessions,
            "ebi_experiment_accessions_study_%s_prep_%s.tsv" % (sid, pid),
        )


class DownloadSampleInfoPerPrep(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, prep_template_id):
        pid = int(prep_template_id)
        pt = PrepTemplate(pid)
        sid = pt.study_id

        self._check_permissions(sid)

        st = SampleTemplate(sid)

        text = st.to_dataframe(samples=list(pt)).to_csv(None, sep="\t")

        self._finish_generate_files("sample_information_from_prep_%s.tsv" % pid, text)


class DownloadUpload(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, path):
        user = self.current_user
        if user.level != "admin":
            raise HTTPError(
                403,
                reason="%s doesn't have access to download uploaded files" % user.email,
            )

        # [0] because it returns a list
        # [1] we only need the filepath
        filepath = get_mountpoint("uploads")[0][1][len(get_db_files_base_dir()) :]
        relpath = join(filepath, path)

        self._write_nginx_placeholder_file(relpath)
        self.set_header("Content-Type", "application/octet-stream")
        self.set_header("Content-Transfer-Encoding", "binary")
        self.set_header("X-Accel-Redirect", "/protected/" + relpath)
        self._set_nginx_headers(basename(relpath))
        self.finish()


class DownloadDataReleaseFromPrep(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, prep_template_id):
        """This method constructs an on the fly ZIP with all the files
        required for a data-prep release/data-delivery. Mainly sample, prep
        info, bioms and coverage
        """
        user = self.current_user
        if user.level not in ("admin", "wet-lab admin"):
            raise HTTPError(
                403,
                reason="%s doesn't have access to download "
                "the data release files" % user.email,
            )

        pid = int(prep_template_id)
        pt = PrepTemplate(pid)
        sid = pt.study_id
        st = SampleTemplate(sid)
        date = datetime.now().strftime("%m%d%y-%H%M%S")
        td = mkdtemp(dir=get_work_base_dir())

        files = []
        readme = [
            f"Delivery created on {date}",
            "",
            f"Host (human) removal: {pt.artifact.human_reads_filter_method}",
            "",
            # this is not changing in the near future so just leaving
            # hardcoded for now
            "Main woltka reference: WoLr2, more info visit: "
            "https://ftp.microbio.me/pub/wol2/",
            "",
            f"Qiita's prep: https://qiita.ucsd.edu/study/description/{sid}"
            f"?prep_id={pid}",
            "",
        ]

        # helper dict to add "user/human" friendly names to the bioms
        human_names = {
            "ec.biom": "KEGG Enzyme (EC)",
            "per-gene.biom": "Per gene Predictions",
            "none.biom": "Per genome Predictions",
            "cell_counts.biom": "Cell counts",
            "pathway.biom": "KEGG Pathway",
            "ko.biom": "KEGG Ontology (KO)",
            "rna_copy_counts.biom": "RNA copy counts",
        }

        # sample-info creation
        fn = join(td, f"sample_information_from_prep_{pid}.tsv")
        readme.append(f"Sample information: {basename(fn)}")
        files.append([fn, basename(fn)])
        st.to_dataframe(samples=list(pt)).to_csv(fn, sep="\t")

        # prep-info creation
        fn = join(td, f"prep_information_{pid}.tsv")
        readme.append(f"Prep information: {basename(fn)}")
        files.append([fn, basename(fn)])
        pt.to_dataframe().to_csv(fn, sep="\t")

        readme.append("")

        # finding the bioms to be added
        bioms = dict()
        coverages = None
        for a in Study(sid).artifacts(artifact_type="BIOM"):
            if a.prep_templates[0].id != pid:
                continue
            biom = None
            for fp in a.filepaths:
                if fp["fp_type"] == "biom":
                    biom = fp
                if coverages is None and "coverages.tgz" == basename(fp["fp"]):
                    coverages = fp["fp"]
            if biom is None:
                continue
            biom_fn = basename(biom["fp"])
            # there is a small but real chance that the same prep has the same
            # artifacts so using the latests
            if biom_fn not in bioms:
                bioms[biom_fn] = [a, biom]
            else:
                if getctime(biom["fp"]) > getctime(bioms[biom_fn][1]["fp"]):
                    bioms[biom_fn] = [a, biom]

        # once we have all the bioms, we can add them to the list of zips
        # and to the readme the biom details and all the processing
        for fn, (a, fp) in bioms.items():
            aname = basename(fp["fp"])
            nname = f"{a.id}_{aname}"
            files.append([fp["fp"], nname])

            hname = ""
            if aname in human_names:
                hname = human_names[aname]
            readme.append(f"{nname}\t{hname}")

            for an in set(a.ancestors.nodes()):
                p = an.processing_parameters
                if p is not None:
                    c = p.command
                    cn = c.name
                    s = c.software
                    sn = s.name
                    sv = s.version
                    pd = p.dump()
                    readme.append(f"\t{cn}\t{sn}\t{sv}\t{pd}")

        # if a coverage was found, add it to the list of files
        if coverages is not None:
            fn = basename(coverages)
            readme.append(f"{fn}\tcoverage files")
            files.append([coverages, fn])

        fn = join(td, "README.txt")
        with open(fn, "w") as fp:
            fp.write("\n".join(readme))
        files.append([fn, basename(fn)])

        zp_fn = f"data_release_{pid}_{date}.zip"
        zp = BytesIO()
        with ZipFile(zp, "w") as zipf:
            for fp, fn in files:
                zipf.write(fp, fn)

        self.set_header("Content-Type", "application/zip")
        self.set_header("Content-Disposition", f"attachment; filename={zp_fn}")
        self.write(zp.getvalue())
        zp.close()
        self.finish()


class DownloadPublicHandler(BaseHandlerDownload):
    @coroutine
    @execute_as_transaction
    def get(self):
        data = self.get_argument("data", None)
        study_id = self.get_argument("study_id", None)
        prep_id = self.get_argument("prep_id", None)
        data_type = self.get_argument("data_type", None)
        dtypes = get_data_types().keys()

        templates = ["sample_information", "prep_information"]
        valid_data = ["raw", "biom"] + templates

        to_download = []
        # for this block to work we need 3 main inputs: prep_id/sample_id, data
        # and data_type - if one is missing raise an error, if both
        # prep_id/sample_id are defined or data_type doesn't exist in qiita
        # we should error
        if (
            data is None
            or (study_id is None and prep_id is None)
            or data not in valid_data
        ):
            raise HTTPError(
                422,
                reason="You need to specify both data (the "
                "data type you want to download - %s) and "
                "study_id or prep_id" % "/".join(valid_data),
            )
        if data_type is not None and data_type not in dtypes:
            raise HTTPError(
                422,
                reason="Not a valid data_type. Valid types are: %s" % ", ".join(dtypes),
            )
        if data in templates and prep_id is None and study_id is None:
            raise HTTPError(
                422,
                reason="If downloading a sample or "
                "preparation file you need to define study_id or"
                " prep_id",
            )

        # if we get here, then we have two main options: templates or raw/biom;
        # however, for raw/biom we need to retrieve the data via the study_id
        # or the prep_id so splitting the next block in study_id/pre_id
        if data in templates:
            if data_type is not None:
                raise HTTPError(
                    422,
                    reason="If requesting an information "
                    "file you cannot specify the data_type",
                )
            elif prep_id is not None and data == "prep_information":
                fname = "preparation_information_%s" % prep_id
                prep_id = int(prep_id)
                try:
                    infofile = PrepTemplate(prep_id)
                except QiitaDBUnknownIDError:
                    raise HTTPError(
                        422, reason="Preparation information does not exist"
                    )
            elif study_id is not None and data == "sample_information":
                fname = "sample_information_%s" % study_id
                study_id = int(study_id)
                try:
                    infofile = SampleTemplate(study_id)
                except QiitaDBUnknownIDError:
                    raise HTTPError(422, reason="Sample information does not exist")
            else:
                raise HTTPError(
                    422, reason="Review your parameters, not a valid combination"
                )
            x = retrieve_filepaths(
                infofile._filepath_table,
                infofile._id_column,
                infofile.id,
                sort="descending",
            )[0]

            basedir = get_db_files_base_dir()
            basedir_len = len(basedir) + 1
            fp = x["fp"][basedir_len:]
            to_download.append((fp, fp, "-", str(x["fp_size"])))
            self._write_nginx_file_list(to_download)

            zip_fn = "%s_%s.zip" % (fname, datetime.now().strftime("%m%d%y-%H%M%S"))
            self._set_nginx_headers(zip_fn)
        else:
            # depending on if we have a study_id or a prep_id, instantiate
            # the study for basic permission validations
            if study_id is not None:
                study_id = int(study_id)
                try:
                    study = Study(study_id)
                except QiitaDBUnknownIDError:
                    raise HTTPError(422, reason="Study does not exist")
                zip_fn = "study_%d_%s_%s.zip" % (
                    study_id,
                    data,
                    datetime.now().strftime("%m%d%y-%H%M%S"),
                )
            else:
                prep_id = int(prep_id)
                try:
                    prep = PrepTemplate(prep_id)
                except QiitaDBUnknownIDError:
                    raise HTTPError(422, reason="Prep does not exist")
                study = Study(prep.study_id)
                zip_fn = "prep_%d_%s_%s.zip" % (
                    prep_id,
                    data,
                    datetime.now().strftime("%m%d%y-%H%M%S"),
                )

            public_raw_download = study.public_raw_download
            # just to be 100% that the data is public, let's start
            # with checking that the study is actually public
            if study.status != "public":
                raise HTTPError(
                    404,
                    reason="Study is not public. If this "
                    "is a mistake contact: %s" % qiita_config.help_email,
                )
            # now let's check that if the data is raw, the study's
            # public_raw_download flag is on
            if data == "raw":
                if not public_raw_download:
                    raise HTTPError(
                        422,
                        reason="No raw data access. If this "
                        "is a mistake contact: %s" % qiita_config.help_email,
                    )
                if study_id is not None:
                    artifacts = [
                        a for a in study.artifacts(dtype=data_type) if not a.parents
                    ]
                else:
                    artifacts = [prep.artifact]
            else:  # this is biom
                if study_id is not None:
                    artifacts = study.artifacts(dtype=data_type, artifact_type="BIOM")
                else:
                    artifacts = [
                        a
                        for a in prep.artifact.descendants.nodes()
                        if a.artifact_type == "BIOM"
                    ]

            # at this point artifacts has all the available artifact
            # so we need to make sure they are public and have no has_human
            # to be added to_download
            for a in artifacts:
                if a.visibility != "public" or a.has_human:
                    continue
                to_download.extend(self._list_artifact_files_nginx(a))

            if not to_download:
                raise HTTPError(
                    422,
                    reason="Nothing to download. If "
                    "this is a mistake contact: %s" % qiita_config.help_email,
                )

        self._write_nginx_file_list(to_download)
        self._set_nginx_headers(zip_fn)
        self.finish()


class DownloadPublicArtifactHandler(BaseHandlerDownload):
    @coroutine
    @execute_as_transaction
    def get(self):
        artifact_id = self.get_argument("artifact_id", None)

        if artifact_id is None:
            raise HTTPError(422, reason="You need to specify an artifact id")
        else:
            try:
                artifact = Artifact(artifact_id)
            except QiitaDBUnknownIDError:
                raise HTTPError(404, reason="Artifact does not exist")
            else:
                if artifact.visibility != "public":
                    raise HTTPError(
                        404,
                        reason="Artifact is not public. If "
                        "this is a mistake contact: %s" % qiita_config.help_email,
                    )
                elif artifact.has_human:
                    raise HTTPError(
                        404,
                        reason="Artifact has possible human "
                        "sequences. If this is a mistake contact: "
                        "%s" % qiita_config.help_email,
                    )
                else:
                    to_download = self._list_artifact_files_nginx(artifact)
                    if not to_download:
                        raise HTTPError(
                            422,
                            reason="Nothing to download. If "
                            "this is a mistake contact: %s" % qiita_config.help_email,
                        )
                    else:
                        self._write_nginx_file_list(to_download)

                        zip_fn = "artifact_%s_%s.zip" % (
                            artifact_id,
                            datetime.now().strftime("%m%d%y-%H%M%S"),
                        )

                        self._set_nginx_headers(zip_fn)
        self.finish()


class DownloadPrivateArtifactHandler(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def post(self, artifact_id):
        # Generate a new download link:
        #   1. Build a signed jwt specifying the user and
        #      the artifact they wish to download
        #   2. Write that jwt to the database keyed by its jti
        #      (jwt ID/ json token identifier)
        #   3. Return the jti as a short url to be used for download

        user = self.current_user
        artifact = Artifact(artifact_id)

        # Check that user is currently allowed to access artifact, else throw
        check_artifact_access(user, artifact)

        # Generate a jwt id as a random uuid in base64
        jti = b64encode(uuid4().bytes).decode("utf-8")
        # Sign a jwt allowing access
        utcnow = datetime.now(timezone.utc)
        jwt = jose_jwt.encode(
            {
                "artifactId": str(artifact_id),
                "perm": "download",
                "sub": str(user._id),
                "email": str(user.email),
                "iat": int(utcnow.timestamp() * 1000),
                "exp": int((utcnow + timedelta(days=7)).timestamp() * 1000),
                "jti": jti,
            },
            qiita_config.jwt_secret,
            algorithm="HS256",
        )

        # Save the jwt to the database
        DownloadLink.create(jwt)

        url = qiita_config.base_url + "/private_download/" + jti
        user_msg = "This link will expire in 7 days on: " + (
            utcnow + timedelta(days=7)
        ).strftime("%Y-%m-%d")

        self.set_status(200)
        self.finish({"url": url, "msg": user_msg})

    @coroutine
    @execute_as_transaction
    def get(self, jti):
        # Grab the jwt out of the database
        jwt = DownloadLink.get(jti)

        # If no jwt, error response
        if jwt is None:
            raise HTTPError(404, reason="Download Not Found.  Link may have expired.")

        # If jwt doesn't validate, error response
        jwt_data = jose_jwt.decode(jwt, qiita_config.jwt_secret, "HS256")
        if jwt_data is None:
            raise HTTPError(403, reason="Invalid JWT")

        # Triple check expiration and user permissions
        user = User(jwt_data["sub"])
        artifact = Artifact(jwt_data["artifactId"])

        utc_millis = datetime.now(timezone.utc).timestamp() * 1000

        if utc_millis < jwt_data["iat"]:
            raise HTTPError(403, reason="This download link is not yet valid")
        if utc_millis > jwt_data["exp"]:
            raise HTTPError(403, reason="This download link has expired")
        if jwt_data["perm"] != "download":
            raise HTTPError(403, reason="This download link is invalid")

        check_artifact_access(user, artifact)

        # All checks out, let's give them the files then!
        to_download = self._list_artifact_files_nginx(artifact)
        if not to_download:
            raise HTTPError(
                422,
                reason="Nothing to download. If "
                "this is a mistake contact: %s" % qiita_config.help_email,
            )
        else:
            self._write_nginx_file_list(to_download)

            zip_fn = "artifact_%s_%s.zip" % (
                jwt_data["artifactId"],
                datetime.now().strftime("%m%d%y-%H%M%S"),
            )

            self._set_nginx_headers(zip_fn)
            self.finish()
