from re import search
from tempfile import mkstemp
from subprocess import call
from shlex import split as shsplit
from glob import glob
from os.path import basename, join, split, isdir, isfile
from os import environ, close, makedirs, remove, listdir
from datetime import date, timedelta
from xml.etree import ElementTree as ET
from xml.dom import minidom
from xml.sax.saxutils import escape
from gzip import GzipFile
from functools import partial

from future.utils import viewitems
from skbio.util import safe_md5, flatten

from qiita_core.qiita_settings import qiita_config
from qiita_ware.exceptions import EBISumbissionError
from qiita_ware.demux import to_per_sample_ascii
from qiita_ware.util import open_file
from qiita_db.logger import LogEntry
from qiita_db.ontology import Ontology
from qiita_db.util import convert_to_id
from qiita_db.study import Study
from qiita_db.data import PreprocessedData
from qiita_db.metadata_template import PrepTemplate, SampleTemplate
from qiita_db.metadata_template.constants import(
    SAMPLE_TEMPLATE_COLUMNS, TARGET_GENE_DATA_TYPES, PREP_TEMPLATE_COLUMNS,
    PREP_TEMPLATE_COLUMNS_TARGET_GENE)


class InvalidMetadataError(Exception):
    """Error that is raised when metadata is not representable as a string"""
    pass


class SampleAlreadyExistsError(Exception):
    """Error that is raised when a sample is added to a submission that already
    has a sample by that name"""
    pass


class NoXMLError(Exception):
    """Error that is raised when the generation of one XML file cannot be
    completed because it depends on another XML file that has not yet been
    generated"""
    pass


def clean_whitespace(s):
    """Standardizes whitespace so that there is only ever one space separating
    tokens"""
    return ' '.join(str(s).split())


class EBISubmission(object):
    """Define an EBI submission, generate submission files and submit

    Submit a preprocessed data to EBI

    The steps for EBI submission are:
    1. Validate that we have all required info to submit
    2. Generate per sample demultiplexed files
    3. Generate XML files for submission
    4. Submit sequences files
    5. Submit XML files. The answer has the EBI submission numbers.

    Parameters
    ----------
    preprocessed_data_id : int
        The preprocesssed data id
    action : str
        The action to perfom, it has to be one of the
        EBISubmission.valid_ebi_actions

    Parameters
    ----------
    preprocessed_data_id : str

    Raises
    ------
    EBISumbissionError
        If either the required columns for EBI and Qiita deploy are not
        present in the sample and prep templates
    """

    valid_ebi_actions = ('ADD', 'VALIDATE', 'MODIFY')
    valid_ebi_submission_states = ('submitting', 'success')
    valid_platforms = ['LS454', 'ILLUMINA', 'UNKNOWN']

    def __init__(self, preprocessed_data_id, action):
        valid_ebi_actions = EBISubmission.valid_ebi_actions
        valid_ebi_submission_states = EBISubmission.valid_ebi_submission_states
        error_msgs = []

        if action not in valid_ebi_actions:
            error_msg = "Not a valid action (%s): %s" % (
                ', '.join(valid_ebi_actions), action)
            LogEntry.create('Runtime', error_msg)
            raise EBISumbissionError(error_msg)

        ena_ontology = Ontology(convert_to_id('ENA', 'ontology'))
        self.action = action
        self.preprocessed_data = PreprocessedData(preprocessed_data_id)
        s = Study(self.preprocessed_data.study)
        self.sample_template = SampleTemplate(s.sample_template)
        self.prep_template = PrepTemplate(self.preprocessed_data.prep_template)

        status = self.preprocessed_data.submitted_to_insdc_status()
        if status in valid_ebi_submission_states:
            error_msg = "Cannot resubmit! Current status is: %s" % status
            LogEntry.create('Runtime', error_msg)
            raise EBISumbissionError(error_msg)

        self.preprocessed_data_id = preprocessed_data_id
        self.study_title = s.title
        self.study_abstract = s.info['study_abstract']

        it = self.prep_template.investigation_type
        if it in ena_ontology.terms:
            self.investigation_type = it
            self.new_investigation_type = None
        elif it in ena_ontology.user_defined_terms:
            self.investigation_type = 'Other'
            self.new_investigation_type = it
        else:
            # This should never happen
            error_msgs.append("Unrecognized investigation type: '%s'. This "
                              "term is neither one of the official terms nor "
                              "one of the user-defined terms in the ENA "
                              "ontology." % it)

        self.ebi_dir = join(qiita_config.working_dir,
                            'ebi_submission_%d' % preprocessed_data_id)
        get_output_fp = partial(join, self.ebi_dir, 'xml_dir')
        self.xml_dir = get_output_fp('')
        self.study_xml_fp = get_output_fp('study.xml')
        self.sample_xml_fp = get_output_fp('sample.xml')
        self.experiment_xml_fp = get_output_fp('experiment.xml')
        self.run_xml_fp = get_output_fp('run.xml')
        self.submission_xml_fp = get_output_fp('submission.xml')
        self.pmids = s.pmids

        # ignore data type for the restrictions as we assume that this was
        # validated in the prep template, here we only going to validate that
        # they exists
        # getting the restrictions
        restrictions = [v.columns.keys()
                        for _, v in viewitems(SAMPLE_TEMPLATE_COLUMNS)]
        restrictions.extend([v.columns.keys()
                             for _, v in viewitems(PREP_TEMPLATE_COLUMNS)])
        if self.prep_template.data_type() in TARGET_GENE_DATA_TYPES:
            restrictions.extend([v.columns.keys() for _, v in
                                 viewitems(PREP_TEMPLATE_COLUMNS_TARGET_GENE)])
        restrictions = set(flatten(restrictions))
        # getting the existing columns
        templates_categories = self.sample_template.categories()
        templates_categories.extend(self.prep_template.categories())
        existing_columms = set(templates_categories)
        missing_columns = restrictions.difference(existing_columms)
        # testing if there are any missing columns
        if missing_columns:
            error_msgs.append(
                "You are missing some columns in study #%d to have a valid "
                "submission #%d: %s." % (s.id, preprocessed_data_id,
                                         ', '.join(list(missing_columns))))

        # generating all samples from sample template
        # self.samples = dict(self.sample_template.items())
        self.samples = {}
        self.samples_prep = {}
        nvp = []
        for k, v in self.sample_template.items():
            if k not in self.prep_template:
                continue
            sample_prep = self.prep_template[k]

            # validating required fields
            if 'platform' not in sample_prep:
                nvp.append(k)
            else:
                platform = sample_prep['platform'].upper()
                if platform not in self.valid_platforms:
                    nvp.append(k)

            self.samples[k] = v
            self.samples_prep[k] = self.prep_template[k]

        if nvp:
            error_msgs.append(
                "These samples from study #%d and preprocessed data #%d do "
                "not have a valid platform: %s" % (s.id, preprocessed_data_id,
                                                   ', '.join(nvp)))
        if error_msgs:
            error_msgs = '\n'.join(error_msgs)
            LogEntry.create('Runtime', error_msgs)
            raise EBISumbissionError(error_msgs)

    def _get_study_alias(self):
        """Format alias using ``self.preprocessed_data_id``"""
        study_alias_format = '%s_ppdid_%s'
        return study_alias_format % (
            qiita_config.ebi_organization_prefix,
            escape(clean_whitespace(str(self.preprocessed_data_id))))

    def _get_sample_alias(self, sample_name):
        """Format alias using ``self.preprocessed_data_id``, `sample_name`"""
        return "%s:%s" % (self._get_study_alias(),
                          escape(clean_whitespace(str(sample_name))))

    def _get_experiment_alias(self, sample_name):
        """Format alias using ``self.preprocessed_data_id``, and `sample_name`

        Currently, this is identical to _get_sample_alias above, since we are
        only going to allow submission of one prep for each sample
        """
        return self._get_sample_alias(sample_name)

    def _get_submission_alias(self):
        """Format alias using ``self.preprocessed_data_id``"""
        safe_preprocessed_data_id = escape(
            clean_whitespace(str(self.preprocessed_data_id)))
        submission_alias_format = '%s_submission_%s'
        return submission_alias_format % (qiita_config.ebi_organization_prefix,
                                          safe_preprocessed_data_id)

    def _get_run_alias(self, file_base_name):
        """Format alias using `file_base_name`
        """
        return '%s_%s_run' % (self._get_study_alias(),
                              basename(file_base_name))

    def _get_library_name(self, sample_name):
        """Format alias using `sample_name`
        """
        return escape(clean_whitespace(sample_name))

    def _add_dict_as_tags_and_values(self, parent_node, attribute_element_name,
                                     data_dict):
        """Format key/value data using a common EBI XML motif"""
        for attr, val in sorted(data_dict.items()):
            attribute_element = ET.SubElement(parent_node,
                                              attribute_element_name)
            tag = ET.SubElement(attribute_element, 'TAG')
            tag.text = clean_whitespace(attr)
            value = ET.SubElement(attribute_element, 'VALUE')
            value.text = clean_whitespace(val)

    def _get_pmid_element(self, study_links, pmid):
        study_link = ET.SubElement(study_links, 'STUDY_LINK')
        xref_link = ET.SubElement(study_link,  'XREF_LINK')

        db = ET.SubElement(xref_link, 'DB')
        db.text = 'PUBMED'

        _id = ET.SubElement(xref_link, 'ID')
        _id.text = str(pmid)

    def generate_study_xml(self):
        """Generates the string for study XML file

        Returns
        -------
        str
            string with study XML values
        """
        study_set = ET.Element('STUDY_SET', {
            'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
            'xsi:noNamespaceSchemaLocation': "ftp://ftp.sra.ebi.ac.uk/meta/xsd"
                                             "/sra_1_3/SRA.study.xsd"})

        study = ET.SubElement(study_set, 'STUDY', {
            'alias': self._get_study_alias(),
            'center_name': qiita_config.ebi_center_name}
        )

        descriptor = ET.SubElement(study, 'DESCRIPTOR')
        study_title = ET.SubElement(descriptor, 'STUDY_TITLE')
        study_title.text = escape(clean_whitespace(self.study_title))

        if self.investigation_type == 'Other':
            ET.SubElement(descriptor, 'STUDY_TYPE', {
                'existing_study_type': 'Other',
                'new_study_type': escape(clean_whitespace(
                    self.new_investigation_type))}
            )
        else:
            ET.SubElement(descriptor, 'STUDY_TYPE', {
                'existing_study_type': escape(clean_whitespace(
                    self.investigation_type))}
            )

        study_abstract = ET.SubElement(descriptor, 'STUDY_ABSTRACT')
        study_abstract.text = clean_whitespace(escape(self.study_abstract))

        # Add pubmed IDs
        if self.pmids:
            study_links = ET.SubElement(study, 'STUDY_LINKS')
            for pmid in self.pmids:
                self._get_pmid_element(study_links, pmid)

        return ET.tostring(study_set)

    def generate_sample_xml(self):
        """Generates the sample XML file

        Returns
        -------
        str
            string with sample XML values
        """
        sample_set = ET.Element('SAMPLE_SET', {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "ftp://ftp.sra.ebi.ac.uk/meta/xsd"
                                             "/sra_1_3/SRA.sample.xsd"})

        for sample_name, sample_info in sorted(viewitems(self.samples)):
            sample_info = dict(sample_info)
            sample = ET.SubElement(sample_set, 'SAMPLE', {
                'alias': self._get_sample_alias(sample_name),
                'center_name': qiita_config.ebi_center_name}
            )

            sample_title = ET.SubElement(sample, 'TITLE')
            sample_title.text = escape(clean_whitespace(sample_name))

            sample_sample_name = ET.SubElement(sample, 'SAMPLE_NAME')
            taxon_id = ET.SubElement(sample_sample_name, 'TAXON_ID')
            text = sample_info.pop('taxon_id')
            taxon_id.text = escape(clean_whitespace(text))

            scientific_name = ET.SubElement(
                sample_sample_name, 'SCIENTIFIC_NAME')
            text = sample_info.pop('scientific_name')
            scientific_name.text = escape(clean_whitespace(text))

            description = ET.SubElement(sample, 'DESCRIPTION')
            text = sample_info.pop('description')
            description.text = escape(clean_whitespace(text))

            if sample_info:
                sample_attributes = ET.SubElement(sample, 'SAMPLE_ATTRIBUTES')
                self._add_dict_as_tags_and_values(sample_attributes,
                                                  'SAMPLE_ATTRIBUTE',
                                                  sample_info)

        return ET.tostring(sample_set)

    def _generate_spot_descriptor(self, design, platform):
        """This XML element (and its subelements) must be written for every
        sample, but its generation depends on only study-level information.
        Therefore, we can break it out into its own method.
        """
        # This section applies only to the LS454 platform
        if platform is not 'LS454':
            return

        # There is some hard-coded information in here, but this is what we
        # have always done in the past...
        spot_descriptor = ET.SubElement(design, 'SPOT_DESCRIPTOR')
        ET.SubElement(spot_descriptor, 'SPOT_DECODE_SPEC')
        read_spec = ET.SubElement(spot_descriptor, 'READ_SPEC')

        read_index = ET.SubElement(read_spec, 'READ_INDEX')
        read_index.text = '0'
        read_class = ET.SubElement(read_spec, 'READ_CLASS')
        read_class.text = 'Application Read'
        read_type = ET.SubElement(read_spec, 'READ_TYPE')
        read_type.text = 'Forward'
        base_coord = ET.SubElement(read_spec, 'BASE_COORD')
        base_coord.text = '1'

    def generate_experiment_xml(self):
        """Generates the experiment XML file

        Returns
        -------
        str
            string with experiment XML values
        """
        study_alias = self._get_study_alias()
        experiment_set = ET.Element('EXPERIMENT_SET', {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "ftp://ftp.sra.ebi.ac.uk/meta/xsd"
                                             "/sra_1_3/SRA.experiment.xsd"})
        for sample_name, sample_prep in sorted(self.samples_prep.items()):
            sample_alias = self._get_sample_alias(sample_name)
            experiment_alias = self._get_experiment_alias(sample_name)
            sample_prep = dict(self.samples_prep[sample_name])

            platform = sample_prep.pop('platform')
            experiment = ET.SubElement(experiment_set, 'EXPERIMENT', {
                'alias': experiment_alias,
                'center_name': qiita_config.ebi_center_name}
            )
            title = ET.SubElement(experiment, 'TITLE')
            title.text = experiment_alias
            ET.SubElement(experiment, 'STUDY_REF', {
                'refname': study_alias}
            )

            design = ET.SubElement(experiment, 'DESIGN')
            design_description = ET.SubElement(design,
                                               'DESIGN_DESCRIPTION')
            edd = sample_prep.pop('experiment_design_description')
            design_description.text = escape(clean_whitespace(edd))
            ET.SubElement(
                design, 'SAMPLE_DESCRIPTOR', {'refname': sample_alias}
            )

            # this is the library contruction section. The only required fields
            # is library_construction_protocol, the other are optional
            library_descriptor = ET.SubElement(design, 'LIBRARY_DESCRIPTOR')
            library_name = ET.SubElement(library_descriptor, 'LIBRARY_NAME')
            library_name.text = self._get_library_name(sample_name)

            lcp = ET.SubElement(library_descriptor,
                                "LIBRARY_CONSTRUCTION_PROTOCOL")
            lcp.text = escape(clean_whitespace(
                sample_prep.pop('library_construction_protocol')))

            # these are not requiered field but present add them in the right
            # format
            if 'library_strategy' in sample_prep:
                library_strategy = ET.SubElement(library_descriptor,
                                                 "LIBRARY_STRATEGY")
                library_strategy.text = sample_prep.pop('library_strategy')
            if 'library_source' in sample_prep:
                library_source = ET.SubElement(library_descriptor,
                                               "LIBRARY_SOURCE")
                library_source.text = sample_prep.pop('library_source')
            if 'library_selection' in sample_prep:
                library_selection = ET.SubElement(library_descriptor,
                                                  "LIBRARY_SELECTION")
                library_selection.text = sample_prep.pop('library_selection')
            if 'library_layout' in sample_prep:
                library_layout = ET.SubElement(library_descriptor,
                                               "LIBRARY_LAYOUT")
                library_layout.text = sample_prep.pop('library_layout')
                # no idea what SINGLE means
                ET.SubElement(library_layout, "SINGLE")

            self._generate_spot_descriptor(design, platform)

            platform_element = ET.SubElement(experiment, 'PLATFORM')
            platform_info = ET.SubElement(platform_element,
                                          platform.upper())
            instrument_model = ET.SubElement(platform_info, 'INSTRUMENT_MODEL')
            instrument_model.text = 'unspecified'

            if sample_prep:
                experiment_attributes = ET.SubElement(
                    experiment, 'EXPERIMENT_ATTRIBUTES')
                self._add_dict_as_tags_and_values(experiment_attributes,
                                                  'EXPERIMENT_ATTRIBUTE',
                                                  sample_prep)

        return ET.tostring(experiment_set)

    def generate_run_xml(self):
        """Generates the run XML file

        Returns
        -------
        str
            string with run XML values
        """
        run_set = ET.Element('RUN_SET', {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "ftp://ftp.sra.ebi.ac.uk/meta/xsd"
                                             "/sra_1_3/SRA.run.xsd"})
        for sample_name, sample_prep in viewitems(self.samples_prep):
            sample_prep = dict(sample_prep)

            experiment_alias = self._get_experiment_alias(sample_name)

            # We only submit fastq
            file_type = 'fastq'
            file_path = join(self.ebi_dir, "%s.fastq.gz" % sample_name)

            with open(file_path) as fp:
                md5 = safe_md5(fp).hexdigest()

            run = ET.SubElement(run_set, 'RUN', {
                'alias': self._get_run_alias(basename(file_path)),
                'center_name': qiita_config.ebi_center_name}
            )
            ET.SubElement(run, 'EXPERIMENT_REF', {
                'refname': experiment_alias}
            )
            data_block = ET.SubElement(run, 'DATA_BLOCK')
            files = ET.SubElement(data_block, 'FILES')
            ET.SubElement(files, 'FILE', {
                'filename': file_path,
                'filetype': file_type,
                'quality_scoring_system': 'phred',
                'checksum_method': 'MD5',
                'checksum': md5}
            )

        return ET.tostring(run_set)

    def generate_submission_xml(self):
        """Generates the submission XML file

        Returns
        -------
        str
            string with run XML values
        """
        submission_set = ET.Element('SUBMISSION_SET', {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "ftp://ftp.sra.ebi.ac.uk/meta/xsd"
                                             "/sra_1_3/SRA.submission.xsd"})
        submission = ET.SubElement(submission_set, 'SUBMISSION', {
            'alias': self._get_submission_alias(),
            'center_name': qiita_config.ebi_center_name}
        )

        actions = ET.SubElement(submission, 'ACTIONS')

        study_action = ET.SubElement(actions, 'ACTION')
        ET.SubElement(study_action, self.action, {
            'schema': 'study',
            'source': basename(self.study_xml_fp)}
        )

        sample_action = ET.SubElement(actions, 'ACTION')
        ET.SubElement(sample_action, self.action, {
            'schema': 'sample',
            'source': basename(self.sample_xml_fp)}
        )

        experiment_action = ET.SubElement(actions, 'ACTION')
        ET.SubElement(experiment_action, self.action, {
            'schema': 'experiment',
            'source': basename(self.experiment_xml_fp)}
        )

        run_action = ET.SubElement(actions, 'ACTION')
        ET.SubElement(run_action, self.action, {
            'schema': 'run', 'source': basename(self.run_xml_fp)}
        )

        if self.action == 'ADD':
            hold_action = ET.SubElement(actions, 'ACTION')
            ET.SubElement(hold_action, 'HOLD', {
                'HoldUntilDate': str(date.today() + timedelta(365))}
            )

        return ET.tostring(submission_set)

    def write_xml_file(self, text, attribute_name, fp):
        """Writes an XML file after calling one of the XML generation
        functions

        Parameters
        ----------
        text : str
            The XML text that will be written
        attribute_name : str
            The name of the attribute in which to store the output filepath
        fp : str
            The filepath to which the XML will be written
        """
        if not isdir(self.xml_dir):
            makedirs(self.xml_dir)

        xml = minidom.parseString(text)

        with open(fp, 'w') as outfile:
            outfile.write(xml.toxml(encoding='UTF-8'))

        setattr(self, attribute_name, fp)

    def generate_curl_command(
            self,
            ebi_seq_xfer_user=qiita_config.ebi_seq_xfer_user,
            ebi_access_key=qiita_config.ebi_access_key,
            ebi_skip_curl_cert=qiita_config.ebi_skip_curl_cert,
            ebi_dropbox_url=qiita_config.ebi_dropbox_url):
        """Generates the curl command for submission

        Parameters
        ----------
        ebi_seq_xfer_user : str
            The user to use when submitting to EBI
        ebi_access_key : str
            The access key issued by EBI for REST submissions
        ebi_skip_curl_cert : bool
            If the curl certificate should be skipped
        ebi_dropbox_url : str
            The dropbox url

        Returns
        -------
        curl_command
            The curl string to be executed

        Notes
        -----
        - All 5 XML files (study, sample, experiment, run, and submission) must
          be generated before executing this function
        """
        # make sure that the XML files have been generated
        url = '?auth=ERA%20{0}%20{1}%3D'.format(ebi_seq_xfer_user,
                                                ebi_access_key)
        curl_command = (
            'curl {0}-F "SUBMISSION=@{1}" -F "STUDY=@{2}" -F "SAMPLE=@{3}" '
            '-F "RUN=@{4}" -F "EXPERIMENT=@{5}" "{6}"'
        ).format(
            '-k ' if ebi_skip_curl_cert else '',
            self.submission_xml_fp,
            self.study_xml_fp,
            self.sample_xml_fp,
            self.run_xml_fp,
            self.experiment_xml_fp,
            join(ebi_dropbox_url, url)
        )

        return curl_command

    def send_sequences(self):
        # Send the sequence files by directory
        unique_dirs = set()
        for f in self.sequence_files:
            basedir, filename = split(f)
            unique_dirs.add(basedir)

        # Set the ASCP password to the one in the Qiita config, but remember
        # the old pass so that we can politely reset it
        old_ascp_pass = environ.get('ASPERA_SCP_PASS', '')
        environ['ASPERA_SCP_PASS'] = qiita_config.ebi_seq_xfer_pass

        for unique_dir in unique_dirs:
            # Get the list of FASTQ files to submit
            fastqs = glob(join(unique_dir, '*.fastq.gz'))

            ascp_command = 'ascp -d -QT -k2 -L- {0} {1}@{2}:./{3}/'.format(
                ' '.join(fastqs), qiita_config.ebi_seq_xfer_user,
                qiita_config.ebi_seq_xfer_url, self.ebi_dir)

            # Generate the command using shlex.split so that we don't have to
            # pass shell=True to subprocess.call
            ascp_command_parts = shsplit(ascp_command)

            # Don't leave the password lingering in the environment if there
            # is any error
            try:
                call(ascp_command_parts)
            finally:
                environ['ASPERA_SCP_PASS'] = old_ascp_pass

    def send_xml(self):
        # Send the XML files
        curl_command = self.generate_curl_command()
        curl_command_parts = shsplit(curl_command)
        temp_fd, temp_fp = mkstemp()
        call(curl_command_parts, stdout=temp_fd)
        close(temp_fd)

        with open(temp_fp, 'U') as curl_output_f:
            curl_result = curl_output_f.read()

        study_accession = None
        submission_accession = None

        if 'success="true"' in curl_result:
            LogEntry.create('Runtime', curl_result)

            print curl_result
            print "SUCCESS"

            accessions = search('<STUDY accession="(?P<study>.+?)".*?'
                                '<SUBMISSION accession="(?P<submission>.+?)"',
                                curl_result)
            if accessions is not None:
                study_accession = accessions.group('study')
                submission_accession = accessions.group('submission')

                LogEntry.create('Runtime', "Study accession:\t%s" %
                                study_accession)
                LogEntry.create('Runtime', "Submission accession:\t%s" %
                                submission_accession)

                print "Study accession:\t", study_accession
                print "Submission accession:\t", submission_accession
            else:
                LogEntry.create('Runtime', ("However, the accession numbers "
                                            "could not be found in the output "
                                            "above."))
                print ("However, the accession numbers could not be found in "
                       "the output above.")
        else:
            LogEntry.create('Fatal', curl_result)
            print curl_result
            print "FAILED"

        return (study_accession, submission_accession)

    def generate_demultiplexed_fastq(self, rewrite_fastq=False, mtime=None):
        """Generates demultiplexed fastq

        Returns
        -------
        demux_samples
            List of successful demultiplexed samples

        Notes
        -----
        - As a performace feature, this method will check if self.ebi_dir
        already exists and, if it does, the script will assume that in a
        previous execution this step was performed correctly and will simply
        read the file names from self.ebi_dir
        """
        ppd = self.preprocessed_data

        if not isdir(self.ebi_dir) or rewrite_fastq:
            makedirs(self.ebi_dir)

            demux = [path for _, path, ftype in ppd.get_filepaths()
                     if ftype == 'preprocessed_demux'][0]

            demux_samples = set()
            with open_file(demux) as demux_fh:
                for s, i in to_per_sample_ascii(demux_fh,
                                                self.sample_template.keys()):
                    sample_fp = join(self.ebi_dir, "%s.fastq.gz" % s)
                    wrote_sequences = False
                    with GzipFile(sample_fp, mode='w', mtime=mtime) as fh:
                        for record in i:
                            fh.write(record)
                            wrote_sequences = True

                    if wrote_sequences:
                        demux_samples.add(s)
                    else:
                        del(self.samples[s])
                        del(self.samples_prep[s])
                        remove(sample_fp)

        else:
            demux_samples = set()
            extension = '.fastq.gz'
            extension_len = len(extension)
            for f in listdir(self.ebi_dir):
                if isfile(join(self.ebi_dir, f)) and f.endswith(extension):
                    demux_samples.add(f[:-extension_len])

            missing_samples = set(self.samples.keys()).difference(
                set(demux_samples))
            for ms in missing_samples:
                del(self.samples[ms])
                del(self.samples_prep[ms])

        return demux_samples
