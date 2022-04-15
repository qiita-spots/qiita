# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from itertools import chain
from os.path import join
from copy import deepcopy
from iteration_utilities import duplicates

from qiita_core.exceptions import IncompetentQiitaDeveloperError
import qiita_db as qdb
from .constants import (PREP_TEMPLATE_COLUMNS, TARGET_GENE_DATA_TYPES,
                        PREP_TEMPLATE_COLUMNS_TARGET_GENE)
from .base_metadata_template import (
    BaseSample, MetadataTemplate, QIITA_COLUMN_NAME)


def _check_duplicated_columns(prep_cols, sample_cols):
    r"""Check for duplicated colums in the prep_cols and sample_cols

    Parameters
    ----------
    prep_cols : list of str
        Column names in the prep info file
    sample_cols : list of str
        Column names in the sample info file

    Raises
    ------
    QiitaDBColumnError
        If there are duplicated columns names in the sample and the prep
    """
    prep_cols.extend(sample_cols)
    dups = set(duplicates(prep_cols))
    if dups:
        raise qdb.exceptions.QiitaDBColumnError(
            'Duplicated column names in the sample and prep info '
            'files: %s. You need to delete that duplicated field' %
            ','.join(dups))


class PrepSample(BaseSample):
    r"""Class that models a sample present in a PrepTemplate.

    See Also
    --------
    BaseSample
    Sample
    """
    _table = "prep_template_sample"
    _table_prefix = "prep_"
    _id_column = "prep_template_id"

    def _check_template_class(self, md_template):
        r"""Checks that md_template is of the correct type

        Parameters
        ----------
        md_template : PrepTemplate
            The metadata template

        Raises
        ------
        IncompetentQiitaDeveloperError
            If `md_template` is not a PrepTemplate object
        """
        if not isinstance(md_template, PrepTemplate):
            raise IncompetentQiitaDeveloperError()


class PrepTemplate(MetadataTemplate):
    r"""Represent the PrepTemplate of a raw data. Provides access to the
    tables in the DB that holds the sample preparation information.

    See Also
    --------
    MetadataTemplate
    SampleTemplate
    """
    _table = "prep_template_sample"
    _table_prefix = "prep_"
    _id_column = "prep_template_id"
    _sample_cls = PrepSample
    _filepath_table = 'prep_template_filepath'
    _forbidden_words = {
                        'sampleid',
                        'qiita_study_id',
                        'qiita_prep_id',
                        QIITA_COLUMN_NAME}

    @classmethod
    def create(cls, md_template, study, data_type, investigation_type=None,
               name=None):
        r"""Creates the metadata template in the database

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples Ids
        study : Study
            The study to which the prep template belongs to.
        data_type : str or int
            The data_type of the prep template
        investigation_type : str, optional
            The investigation type, if relevant
        name : str, optional
            The prep template name

        Returns
        -------
        A new instance of `cls` to access to the PrepTemplate stored in the DB

        Raises
        ------
        QiitaDBColumnError
            If the investigation_type is not valid
            If a required column is missing in md_template
        """
        with qdb.sql_connection.TRN:
            # If the investigation_type is supplied, make sure it is one of
            # the recognized investigation types
            if investigation_type is not None:
                cls.validate_investigation_type(investigation_type)

            # Check if the data_type is the id or the string
            if isinstance(data_type, int):
                data_type_id = data_type
                data_type_str = qdb.util.convert_from_id(data_type,
                                                         "data_type")
            else:
                data_type_id = qdb.util.convert_to_id(data_type, "data_type")
                data_type_str = data_type

            pt_cols = PREP_TEMPLATE_COLUMNS
            if data_type_str in TARGET_GENE_DATA_TYPES:
                pt_cols = deepcopy(PREP_TEMPLATE_COLUMNS)
                pt_cols.update(PREP_TEMPLATE_COLUMNS_TARGET_GENE)

            md_template = cls._clean_validate_template(md_template, study.id)
            _check_duplicated_columns(list(md_template.columns),
                                      study.sample_template.categories)

            # check that we are within the limit of number of samples
            ms = cls.max_samples()
            nsamples = md_template.shape[0]
            if ms is not None and nsamples > ms:
                raise ValueError(f"{nsamples} exceeds the max allowed number "
                                 f"of samples: {ms}")

            # Insert the metadata template
            sql = """INSERT INTO qiita.prep_template
                        (data_type_id, investigation_type)
                     VALUES (%s, %s)
                     RETURNING prep_template_id"""
            qdb.sql_connection.TRN.add(sql, [data_type_id, investigation_type])
            prep_id = qdb.sql_connection.TRN.execute_fetchlast()

            try:
                cls._common_creation_steps(md_template, prep_id)
            except Exception:
                # Check if sample IDs present here but not in sample template
                sql = """SELECT sample_id from qiita.study_sample
                         WHERE study_id = %s"""
                # Get list of study sample IDs, prep template study IDs,
                # and their intersection
                qdb.sql_connection.TRN.add(sql, [study.id])
                prep_samples = set(md_template.index.values)
                unknown_samples = prep_samples.difference(
                    qdb.sql_connection.TRN.execute_fetchflatten())
                if unknown_samples:
                    raise qdb.exceptions.QiitaDBExecutionError(
                        'Samples found in prep template but not sample '
                        'template: %s' % ', '.join(unknown_samples))

                # some other error we haven't seen before so raise it
                raise

            # Link the prep template with the study
            sql = """INSERT INTO qiita.study_prep_template
                        (study_id, prep_template_id)
                     VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, [study.id, prep_id])

            qdb.sql_connection.TRN.execute()

            pt = cls(prep_id)
            pt.validate(pt_cols)
            pt.generate_files()

            # Add the name to the prep information
            pt.name = (name if name is not None
                       else "Prep information %s" % pt.id)

            return pt

    @classmethod
    def validate_investigation_type(self, investigation_type):
        """Simple investigation validation to avoid code duplication

        Parameters
        ----------
        investigation_type : str
            The investigation type, should be part of the ENA ontology

        Raises
        -------
        QiitaDBColumnError
            The investigation type is not in the ENA ontology
        """
        with qdb.sql_connection.TRN:
            ontology = qdb.ontology.Ontology(
                qdb.util.convert_to_id('ENA', 'ontology'))
            terms = ontology.terms + ontology.user_defined_terms
            if investigation_type not in terms:
                raise qdb.exceptions.QiitaDBColumnError(
                    "'%s' is Not a valid investigation_type. Choose from: %s"
                    % (investigation_type, ', '.join(terms)))

    @classmethod
    def delete(cls, id_):
        r"""Deletes the table from the database

        Parameters
        ----------
        id_ : obj
            The object identifier

        Raises
        ------
        QiitaDBExecutionError
            If the prep template already has an artifact attached
        QiitaDBUnknownIDError
            If no prep template with id = id_ exists
        """
        with qdb.sql_connection.TRN:
            table_name = cls._table_name(id_)

            if not cls.exists(id_):
                raise qdb.exceptions.QiitaDBUnknownIDError(id_, cls.__name__)

            sql = """SELECT (
                        SELECT artifact_id
                        FROM qiita.prep_template
                        WHERE prep_template_id=%s)
                    IS NOT NULL"""
            args = [id_]
            qdb.sql_connection.TRN.add(sql, args)
            artifact_attached = qdb.sql_connection.TRN.execute_fetchlast()
            if artifact_attached:
                raise qdb.exceptions.QiitaDBExecutionError(
                    "Cannot remove prep template %d because it has an artifact"
                    " associated with it" % id_)

            # Delete the prep template filepaths
            sql = """DELETE FROM qiita.prep_template_filepath
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, args)

            # Drop the prep_X table
            sql = "DROP TABLE qiita.{0}".format(table_name)
            qdb.sql_connection.TRN.add(sql)

            # Remove the rows from prep_template_samples
            sql = "DELETE FROM qiita.{0} WHERE {1} = %s".format(
                cls._table, cls._id_column)
            qdb.sql_connection.TRN.add(sql, args)

            # Remove the row from study_prep_template
            sql = """DELETE FROM qiita.study_prep_template
                     WHERE {0} = %s""".format(cls._id_column)
            qdb.sql_connection.TRN.add(sql, args)

            # Remove the row from prep_template
            sql = "DELETE FROM qiita.prep_template WHERE {0} = %s".format(
                cls._id_column)
            qdb.sql_connection.TRN.add(sql, args)

            qdb.sql_connection.TRN.execute()

    def data_type(self, ret_id=False):
        """Returns the data_type or the data_type id

        Parameters
        ----------
        ret_id : bool, optional
            If true, return the id instead of the string, default false.

        Returns
        -------
        str or int
            string value of data_type or data_type_id if ret_id is True
        """
        with qdb.sql_connection.TRN:
            ret = "_id" if ret_id else ""
            sql = """SELECT d.data_type{0}
                     FROM qiita.data_type d
                        JOIN qiita.prep_template p
                            ON p.data_type_id = d.data_type_id
                     WHERE p.prep_template_id=%s""".format(ret)
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def columns_restrictions(self):
        """Gets the dictionary of colums required based on data_type

        Returns
        -------
        dict
            The dict of restictions based on the data_type
        """
        pt_cols = deepcopy(PREP_TEMPLATE_COLUMNS)
        if self.data_type() in TARGET_GENE_DATA_TYPES:
            pt_cols.update(PREP_TEMPLATE_COLUMNS_TARGET_GENE)

        return pt_cols

    def can_be_updated(self, columns):
        """Whether the template can be updated or not

        Parameters
        ----------
        columns : set
            A set of the names of the columns to be updated

        Returns
        -------
        bool
            If the template can be updated

        Notes
        -----
        The prep template can be updated when (1) it has no preprocessed data
        or the prep template data-type is not part of TARGET_GENE_DATA_TYPES,
        (2) if is part of TARGET_GENE_DATA_TYPES then we will only update if
        the columns being updated are not part of
        PREP_TEMPLATE_COLUMNS_TARGET_GENE
        """
        with qdb.sql_connection.TRN:
            if self.data_type() not in TARGET_GENE_DATA_TYPES:
                return True

            artifact = self.artifact
            if not artifact:
                return True

            sql = """SELECT EXISTS(SELECT *
                                   FROM qiita.parent_artifact
                                   WHERE parent_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [artifact.id])
            if not qdb.sql_connection.TRN.execute_fetchlast():
                return True

            tg_columns = set(chain.from_iterable(
                [v.columns for v in
                 PREP_TEMPLATE_COLUMNS_TARGET_GENE.values()]))

            if not columns & tg_columns:
                return True

            return False

    def can_be_extended(self, new_samples, new_columns):
        """Whether the template can be extended or not

        Parameters
        ----------
        new_samples : list of str
            The new samples to be added to the template
        new_columns : list of str
            The new columns to be added to the template

        Returns
        -------
        bool
            Whether the template can be extended or not
        str
            The error message in case that it can't be extended

        Notes
        -----
        New samples can't be added to the prep template if a preprocessed
        data has been already generated.
        """
        if new_samples:
            with qdb.sql_connection.TRN:
                artifact = self.artifact
                if artifact:
                    sql = """SELECT EXISTS(SELECT *
                                           FROM qiita.parent_artifact
                                           WHERE parent_id = %s)"""
                    qdb.sql_connection.TRN.add(sql, [artifact.id])
                    if qdb.sql_connection.TRN.execute_fetchlast():
                        return False, ("The artifact attached to the prep "
                                       "template has already been processed. "
                                       "No new samples can be added to the "
                                       "prep template")

        _check_duplicated_columns(list(new_columns), qdb.study.Study(
            self.study_id).sample_template.categories)

        return True, ""

    @property
    def artifact(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_id
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            result = qdb.sql_connection.TRN.execute_fetchlast()
            if result:
                return qdb.artifact.Artifact(result)
            return None

    @artifact.setter
    def artifact(self, artifact):
        with qdb.sql_connection.TRN:
            sql = """SELECT (SELECT artifact_id
                             FROM qiita.prep_template
                             WHERE prep_template_id = %s)
                     IS NOT NULL"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            if qdb.sql_connection.TRN.execute_fetchlast():
                raise qdb.exceptions.QiitaDBError(
                    "Prep template %d already has an artifact associated"
                    % self.id)
            sql = """UPDATE qiita.prep_template
                     SET artifact_id = %s
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [artifact.id, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def investigation_type(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT investigation_type FROM qiita.prep_template
                     WHERE {0} = %s""".format(self._id_column)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @investigation_type.setter
    def investigation_type(self, investigation_type):
        r"""Update the investigation type

        Parameters
        ----------
        investigation_type : str
            The investigation type to set, should be part of the ENA ontology

        Raises
        ------
        QiitaDBColumnError
            If the investigation type is not a valid ENA ontology
        """
        if investigation_type is not None:
            self.validate_investigation_type(investigation_type)

        sql = """UPDATE qiita.prep_template SET investigation_type = %s
                 WHERE {0} = %s""".format(self._id_column)
        qdb.sql_connection.perform_as_transaction(
            sql, [investigation_type, self.id])

    @property
    def study_id(self):
        """Gets the study id with which this prep template is associated

        Returns
        -------
        int
            The ID of the study with which this prep template is associated
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT study_id FROM qiita.study_prep_template
                     WHERE prep_template_id=%s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def deprecated(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT deprecated FROM qiita.prep_template
                     WHERE {0} = %s""".format(self._id_column)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @deprecated.setter
    def deprecated(self, deprecated):
        r"""Update deprecated value of prep information file

        Parameters
        ----------
        deprecated : bool
            If the prep info file is deprecated
        """
        sql = """UPDATE qiita.prep_template SET deprecated = %s
                 WHERE {0} = %s""".format(self._id_column)
        qdb.sql_connection.perform_as_transaction(sql, [deprecated, self.id])

    def generate_files(self, samples=None, columns=None):
        r"""Generates all the files that contain data from this template

        Parameters
        ----------
        samples : iterable of str, optional
            The samples that were added/updated
        columns : iterable of str, optional
            The columns that were added/updated
        """
        with qdb.sql_connection.TRN:
            # figuring out the filepath of the prep template
            _id, fp = qdb.util.get_mountpoint('templates')[0]
            # update timestamp in the DB first
            qdb.sql_connection.TRN.add(
                """UPDATE qiita.prep_template
                   SET modification_timestamp = CURRENT_TIMESTAMP
                   WHERE prep_template_id = %s""", [self._id])
            ctime = self.modification_timestamp
            fp = join(fp, '%d_prep_%d_%s.txt' % (self.study_id, self._id,
                      ctime.strftime("%Y%m%d-%H%M%S")))
            # storing the template
            self.to_file(fp)
            # adding the fp to the object
            fp_id = qdb.util.convert_to_id("prep_template", "filepath_type")
            self.add_filepath(fp, fp_id=fp_id)

    @property
    def status(self):
        """The status of the prep template

        Returns
        -------
        str
            The status of the prep template

        Notes
        -----
        The status of a prep template is inferred by the status of the
        processed data generated from this prep template. If no processed
        data has been generated with this prep template; then the status
        is 'sandbox'.
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT visibility
                     FROM qiita.prep_template
                        JOIN qiita.artifact USING (artifact_id)
                        JOIN qiita.visibility USING (visibility_id)
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])

            return qdb.util.infer_status(
                qdb.sql_connection.TRN.execute_fetchindex())

    @property
    def qiime_map_fp(self):
        """The QIIME mapping filepath attached to the prep template

        Returns
        -------
        str
            The filepath of the QIIME mapping file
        """
        for x in qdb.util.retrieve_filepaths(
                self._filepath_table, self._id_column, self.id,
                sort='descending'):
            if x['fp_type'] == 'qiime_map':
                return x['fp']

    @property
    def ebi_experiment_accessions(self):
        """The EBI experiment accessions for the samples in the prep template

        Returns
        -------
        dict of {str: str}
            The EBI experiment accessions numbers keyed by sample id
        """
        return self._get_accession_numbers('ebi_experiment_accession')

    @ebi_experiment_accessions.setter
    def ebi_experiment_accessions(self, value):
        """Sets the EBI experiment accessions

        Parameters
        ----------
        values : dict of {str: str}
            The EBI experiment accessions, keyed by sample id

        Raises
        ------
        QiitaDBError
            If a sample in `value` already has an accession number
        """
        self._update_accession_numbers('ebi_experiment_accession', value)

    @property
    def is_submitted_to_ebi(self):
        """Inquires if the prep template has been submitted to EBI or not

        Returns
        -------
        bool
            True if the prep template has been submitted to EBI,
            false otherwise
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT sample_id, ebi_experiment_accession
                        FROM qiita.{0}
                        WHERE {1}=%s
                            AND ebi_experiment_accession IS NOT NULL)
                  """.format(self._table, self._id_column)
            qdb.sql_connection.TRN.add(sql, [self.id])
            is_submitted = qdb.sql_connection.TRN.execute_fetchlast()
        return is_submitted

    def delete_samples(self, sample_names):
        """Delete `sample_names` from prep information file

        Parameters
        ----------
        sample_names : list of str
            The sample names to be deleted

        Raises
        ------
        QiitaDBColumnError
            If the prep info file has been processed
        """
        if self.artifact:
            raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                "Prep info file '%d' has files attached, you cannot delete "
                "samples." % (self._id))

        self._common_delete_sample_steps(sample_names)

    @property
    def name(self):
        """The name of the prep information

        Returns
        -------
        str
            The name of the prep information
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT name
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @name.setter
    def name(self, value):
        """Changes the name of the prep template"""
        sql = """UPDATE qiita.prep_template
                 SET name = %s
                 WHERE prep_template_id = %s"""
        qdb.sql_connection.perform_as_transaction(sql, [value, self.id])

    def to_dataframe(self, add_ebi_accessions=False):
        """Returns the metadata template as a dataframe

        Parameters
        ----------
        add_ebi_accessions : bool, optional
            If this should add the ebi accessions
        """
        df = self._common_to_dataframe_steps()

        if add_ebi_accessions:
            accessions = self.ebi_experiment_accessions
            df['qiita_ebi_experiment_accessions'] = df.index.map(
                lambda sid: accessions[sid])

        return df

    @property
    def creation_timestamp(self):
        """The creation timestamp of the prep information

        Returns
        -------
        datetime.datetime
            The creation timestamp of the prep information
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT creation_timestamp
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def modification_timestamp(self):
        """The modification timestamp of the prep information

        Returns
        -------
        datetime.datetime
            The modification timestamp of the prep information
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT modification_timestamp
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @staticmethod
    def max_samples():
        return qdb.util.max_preparation_samples()

    def add_default_workflow(self, user):
        """The modification timestamp of the prep information

        Parameters
        ----------
        user : qiita_db.user.User
            The user that requested to add the default workflows

        Returns
        -------
        ProcessingWorkflow
            The workflow created

        Raises
        ------
        ValueError
            a. If this preparation doesn't have valid workflows
            b. This preparation has been fully processed (no new steps needed)
            c. If there is no valid initial artifact to start the workflow
        """
        # helper functions to avoid duplication of code

        def _get_node_info(workflow, node):
            # retrieves the merging scheme of a node
            parent = list(workflow.graph.predecessors(node))
            if parent:
                parent = parent.pop()
                pdp = parent.default_parameter
                pcmd = pdp.command
                pparams = pdp.values
            else:
                pcmd = None
                pparams = {}

            dp = node.default_parameter
            cparams = dp.values
            ccmd = dp.command

            parent_cmd_name = None
            parent_merging_scheme = None
            if pcmd is not None:
                parent_cmd_name = pcmd.name
                parent_merging_scheme = pcmd.merging_scheme

            return qdb.util.human_merging_scheme(
                ccmd.name, ccmd.merging_scheme, parent_cmd_name,
                parent_merging_scheme, cparams, [], pparams)

        def _get_predecessors(workflow, node):
            # recursive method to get predecessors of a given node
            pred = []
            for pnode in workflow.graph.predecessors(node):
                pred = _get_predecessors(workflow, pnode)
                cxns = {x[0]: x[2]
                        for x in workflow.graph.get_edge_data(
                            pnode, node)['connections'].connections}
                data = [pnode, node, cxns]
                if pred is None:
                    pred = [data]
                else:
                    pred.append(data)
                return pred

        # Note: we are going to use the final BIOMs to figure out which
        #       processing is missing from the back/end to the front, as this
        #       will prevent generating unnecessary steps (AKA already provided
        #       by another command), like "Split Library of Demuxed",
        #       when "Split per Sample" is alrady generated
        #
        # The steps to generate the default workflow are as follow:
        # 1. retrieve all valid merging schemes from valid jobs in the
        #    current preparation
        # 2. retrive all the valid workflows for the preparation data type and
        #    find the final BIOM missing from the valid available merging
        #    schemes
        # 3. loop over the missing merging schemes and create the commands
        #    missing to get to those processed samples and add them to a new
        #    workflow

        # 1.
        prep_jobs = [j for c in self.artifact.descendants.nodes()
                     for j in c.jobs(show_hidden=True)
                     if j.command.software.type == 'artifact transformation']
        merging_schemes = {
            qdb.archive.Archive.get_merging_scheme_from_job(j): {
                x: y.id for x, y in j.outputs.items()}
            # we are going to select only the jobs that were a 'success', that
            # are not 'hidden' and that have an output - jobs that are not
            # hidden and a successs but that do not have outputs are jobs which
            # resulting artifacts (outputs) were deleted
            for j in prep_jobs if j.status == 'success' and not j.hidden
            and j.outputs}

        # 2.
        pt_dt = self.data_type()
        pt_artifact = self.artifact.artifact_type
        workflows = [wk for wk in qdb.software.DefaultWorkflow.iter()
                     if wk.artifact_type == pt_artifact and
                     pt_dt in wk.data_type]
        if not workflows:
            # raises option a.
            msg = (f'This preparation data type: "{pt_dt}" and/or artifact '
                   f'type "{pt_artifact}" does not have valid workflows')
            raise ValueError(msg)
        missing_artifacts = dict()
        for wk in workflows:
            missing_artifacts[wk] = dict()
            for node, degree in wk.graph.out_degree():
                if degree != 0:
                    continue
                mscheme = _get_node_info(wk, node)
                if mscheme not in merging_schemes:
                    missing_artifacts[wk][mscheme] = node
            if not missing_artifacts[wk]:
                del missing_artifacts[wk]
        if not missing_artifacts:
            # raises option b.
            raise ValueError('This preparation is complete')

        # 3.
        workflow = None
        for wk, wk_data in missing_artifacts.items():
            previous_jobs = dict()
            for ma, node in wk_data.items():
                predecessors = _get_predecessors(wk, node)
                predecessors.reverse()
                cmds_to_create = []
                init_artifacts = None
                for i, (pnode, cnode, cxns) in enumerate(predecessors):
                    cdp = cnode.default_parameter
                    cdp_cmd = cdp.command
                    params = cdp.values.copy()

                    icxns = {y: x for x, y in cxns.items()}
                    reqp = {x: icxns[y[1][0]]
                            for x, y in cdp_cmd.required_parameters.items()}
                    cmds_to_create.append([cdp_cmd, params, reqp])

                    info = _get_node_info(wk, pnode)
                    if info in merging_schemes:
                        if set(merging_schemes[info]) >= set(cxns):
                            init_artifacts = merging_schemes[info]
                            break
                if init_artifacts is None:
                    pdp = pnode.default_parameter
                    pdp_cmd = pdp.command
                    params = pdp.values.copy()
                    # verifying that the workflow.artifact_type is included
                    # in the command input types or raise an error
                    wkartifact_type = wk.artifact_type
                    reqp = dict()
                    for x, y in pdp_cmd.required_parameters.items():
                        if wkartifact_type not in y[1]:
                            raise ValueError(f'{wkartifact_type} is not part '
                                             'of this preparation and cannot '
                                             'be applied')
                        reqp[x] = wkartifact_type

                    cmds_to_create.append([pdp_cmd, params, reqp])

                    init_artifacts = {wkartifact_type: self.artifact.id}

                cmds_to_create.reverse()
                current_job = None
                for i, (cmd, params, rp) in enumerate(cmds_to_create):
                    previous_job = current_job
                    if previous_job is None:
                        req_params = dict()
                        for iname, dname in rp.items():
                            if dname not in init_artifacts:
                                msg = (f'Missing Artifact type: "{dname}" in '
                                       'this preparation; this might be due '
                                       'to missing steps or not having the '
                                       'correct raw data.')
                                # raises option c.
                                raise ValueError(msg)
                            req_params[iname] = init_artifacts[dname]
                    else:
                        req_params = dict()
                        connections = dict()
                        for iname, dname in rp.items():
                            req_params[iname] = f'{previous_job.id}{dname}'
                            connections[dname] = iname
                    params.update(req_params)
                    job_params = qdb.software.Parameters.load(
                        cmd, values_dict=params)

                    if params in previous_jobs.values():
                        for x, y in previous_jobs.items():
                            if params == y:
                                current_job = x
                    else:
                        if workflow is None:
                            PW = qdb.processing_job.ProcessingWorkflow
                            workflow = PW.from_scratch(user, job_params)
                            current_job = [
                                j for j in workflow.graph.nodes()][0]
                        else:
                            if previous_job is None:
                                current_job = workflow.add(
                                    job_params, req_params=req_params)
                            else:
                                current_job = workflow.add(
                                    job_params, req_params=req_params,
                                    connections={previous_job: connections})
                        previous_jobs[current_job] = params

        return workflow
