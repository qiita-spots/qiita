from re import search
from tempfile import mkstemp
from subprocess import call
from shlex import split as shsplit
from glob import glob
from os.path import basename, exists, join, split
from os import environ, close
from datetime import date, timedelta, datetime
from xml.etree import ElementTree as ET
from xml.dom import minidom
from xml.sax.saxutils import escape

from future.utils import viewitems
from skbio.util import safe_md5

from qiita_core.qiita_settings import qiita_config
from qiita_ware.exceptions import EBISumbissionError
from qiita_db.logger import LogEntry
from qiita_db.ontology import Ontology
from qiita_db.util import convert_to_id
from qiita_db.study import Study
from qiita_db.data import PreprocessedData
from qiita_db.metadata_template import PrepTemplate


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
    return ' '.join(s.split())


def iter_file_via_list_of_dicts(input_file):
    """Iterates over a TSV file, yielding dicts keyed by the column headers

    Parameters
    ----------
    input_file : file
        The file to iterate over

    Returns
    -------
    generator
        Yields dicts keyed by the column headers

    Notes
    -----
    - Assumes the first line contains the column headers
    - Assumes no duplicate column headers
    - All column headers will be transformed to lowercase
    - Skips lines containing only whitespace
    """
    header_line = input_file.readline()
    header_line = header_line.lstrip('#')
    headers = [x.strip().lower() for x in header_line.split('\t')]
    for line in input_file:
        line = line.strip()
        if not line:
            continue

        line_elements = line.split('\t')
        yield dict(zip(headers, line_elements))


class EBISubmission(object):
    """Define an EBI submission, generate submission files and submit

    Submit a preprocessed data to EBI

    The steps for EBI submission are:
    1. Validate that the submission status is different than
    self.valid_ebi_actions and that there is a valid investigation_type
    2. Generate per sample demultiplexed files
    3. Generate XML files for submission
    4. Submit sequences files
    5. Submit XML files. The answer has the EBI submission numbers.

    Parameters
    ----------
    preprocessed_data_id : int
        The preprocesssed data id
    action : str
        The action to perfom, it has to be one of the self.valid_ebi_actions

    Parameters
    ----------
    preprocessed_data_id : str
    """
    def __init__(self, preprocessed_data_id, action, **kwargs):
        self.valid_ebi_actions = ('ADD', 'VALIDATE', 'MODIFY')
        self.valid_ebi_submission_states = ('submitting', 'success')

        # Step 1: variable setup and validations
        if action not in self.valid_ebi_actions:
            raise ValueError("Not a valid action (%s): %s" % (
                ', '.join(self.valid_ebi_actions), action))

        ena_ontology = Ontology(convert_to_id('ENA', 'ontology'))
        ppd = PreprocessedData(preprocessed_data_id)
        s = Study(ppd.study)
        pt = PrepTemplate(ppd.prep_template)

        status = ppd.submitted_to_insdc_status()
        if status in self.valid_ebi_submission_states:
            raise ValueError("Cannot resubmit! Current status is: %s" % status)

        self.preprocessed_data_id = preprocessed_data_id
        self.study_title = s.title
        self.study_abstract = s.info['study_abstract']

        it = pt.investigation_type
        key = it
        if it in ena_ontology.terms:
            self.investigation_type = it
            self.new_investigation_type = None
        elif it in ena_ontology.user_defined_terms:
            self.investigation_type = 'Other'
            self.new_investigation_type = it
        else:
            # This should never happen
            raise ValueError("Unrecognized investigation type: '%s'. This "
                             "term is neither one of the official terms nor "
                             "one of the user-defined terms in the ENA "
                             "ontology")
        ts = datetime.now().strftime('%Y_%m_%d_%H:%M:%S')
        self.ebi_dir = '%s_%s' % (preprocessed_data_id, ts)
        self.sequence_files = []
        self.study_xml_fp = None
        self.sample_xml_fp = None
        self.experiment_xml_fp = None
        self.run_xml_fp = None
        self.submission_xml_fp = None
        self.pmids = s.pmids

        # dicts that map investigation_type to library attributes
        lib_strategies = {'metagenome': 'POOLCLONE',
                          'mimarks-survey': 'AMPLICON'}
        lib_selections = {'mimarks-survey': 'PCR'}
        lib_sources = {}

        self.library_strategy = lib_strategies.get(key, "OTHER")
        self.library_source = lib_sources.get(key, "METAGENOMIC")
        self.library_selection = lib_selections.get(key, "unspecified")

        # This will hold the submission's samples, keyed by the sample name
        self.samples = {}

    def _stringify_kwargs(self, kwargs_dict):
        """Turns values in a dictionay into strings, None, or self.empty_value
        """
        try:
            result = {
                str(k): str(v) if v is not None else self.empty_value
                for k, v in viewitems(kwargs_dict)}
            return result
        except ValueError:
            raise InvalidMetadataError("All additional metadata passed via "
                                       "kwargs to the EBISubmission "
                                       "constructor must be representatable "
                                       "as strings.")

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
        """Generates the study XML file

        Returns
        -------
        xml.etree.Element
            The root elelement of the generated ``ElementTree``
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

        return study_set

    def add_sample(self, sample_name, taxon_id, scientific_name,
                   description, **kwargs):
        """Adds sample information to the current submission

        Parameters
        ----------
        sample_name : str
            Unique identifier for the sample
        taxon_id : str
            NCBI's taxon ID for the sample
        scientific_name : str
            NCBI's scientific name for the `taxon_id`
        description : str

            Defaults to ``None``. If not provided, the `empty_value` will be
            used for the description

        Raises
        ------
        SampleAlreadyExistsError
            If `sample_name` already exists in the ``samples`` dict
        """
        if sample_name in self.samples:
            raise SampleAlreadyExistsError("Two samples with the same "
                                           "sample_name cannot be added to "
                                           "the same submission. "
                                           "(sample_name: %s)" % sample_name)

        self.samples[sample_name] = {}

        self.samples[sample_name]['taxon_id'] = escape(
            clean_whitespace(taxon_id))

        self.samples[sample_name]['scientific_name'] = escape(
            clean_whitespace(scientific_name))

        self.samples[sample_name]['description'] = escape(
            clean_whitespace(description))

        self.samples[sample_name]['attributes'] = self._stringify_kwargs(
            kwargs)

        self.samples[sample_name]['prep'] = None

    def generate_sample_xml(self):
        """Generates the sample XML file

        Returns
        -------
        xml.etree.Element
            The root elelement of the generated ``ElementTree``
        """
        sample_set = ET.Element('SAMPLE_SET', {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "ftp://ftp.sra.ebi.ac.uk/meta/xsd"
                                             "/sra_1_3/SRA.sample.xsd"})

        for sample_name, sample_info in sorted(viewitems(self.samples)):
            sample = ET.SubElement(sample_set, 'SAMPLE', {
                'alias': self._get_sample_alias(sample_name),
                'center_name': qiita_config.ebi_center_name}
            )

            sample_title = ET.SubElement(sample, 'TITLE')
            sample_title.text = escape(clean_whitespace(sample_name))

            sample_name_element = ET.SubElement(sample, 'SAMPLE_NAME')
            taxon_id = ET.SubElement(sample_name_element, 'TAXON_ID')
            taxon_id.text = escape(clean_whitespace(sample_info['taxon_id']))

            taxon_id = ET.SubElement(sample_name_element, 'SCIENTIFIC_NAME')
            taxon_id.text = escape(
                clean_whitespace(sample_info['scientific_name']))

            description = ET.SubElement(sample, 'DESCRIPTION')
            description.text = escape(clean_whitespace(
                sample_info['description']))

            if sample_info['attributes']:
                sample_attributes = ET.SubElement(sample, 'SAMPLE_ATTRIBUTES')
                self._add_dict_as_tags_and_values(sample_attributes,
                                                  'SAMPLE_ATTRIBUTE',
                                                  sample_info['attributes'])

        return sample_set

    def add_sample_prep(self, sample_name, platform, file_type, file_path,
                        experiment_design_description,
                        library_construction_protocol,
                        **kwargs):
        """Add prep info for an existing sample

        Parameters
        ----------
        sample_name : str
            The `sample_name` must exist in the ``samples`` list
        platform : {'LS454', 'ILLUMINA', 'UNKNOWN'}
            The sequencing platform
        file_type : {'sff', 'fastq', 'fasta'}
            The type of file
        file_path : str
            The path to the sequence file for this sample
        experiment_design_description : str
        library_construction_protocol : str

        Raises
        ------
        KeyError
            If `sample_name` is not in the list of samples in the
            ``EBISubmission`` object
        KeyError
            If there is already prep info associated with the specified sample
        ValueError
            If the platform is not one of the recognized platforms
        """
        if sample_name not in self.samples:
            raise KeyError("Sample %s: sample has not yet been associated "
                           "with the submission.")

        if self.samples[sample_name]['prep']:
            raise KeyError("Sample %s: multiple rows in prep with this sample "
                           "id!" % sample_name)

        platforms = ['LS454', 'ILLUMINA', 'UNKNOWN']
        if platform.upper() not in platforms:
            raise ValueError("The platform name %s is invalid, must be one of "
                             "%s (case insensitive)" % (platform,
                                                        ', '.join(platforms)))

        self.sequence_files.append(file_path)
        prep_info = self._stringify_kwargs(kwargs)
        if prep_info is None:
            prep_info = {}
        prep_info['platform'] = platform
        prep_info['file_type'] = file_type
        prep_info['file_path'] = file_path
        prep_info['experiment_design_description'] = \
            experiment_design_description
        prep_info['library_construction_protocol'] = \
            library_construction_protocol

        self.samples[sample_name]['prep'] = prep_info

    def _generate_library_descriptor(self, design, sample_name,
                                     library_construction_protocol):
        """This XML element (and its subelements) must be written for every
        sample, but its generation depends on only study-level information.
        Therefore, we can break it out into its own method.
        """

        library_descriptor = ET.SubElement(design, 'LIBRARY_DESCRIPTOR')
        library_name = ET.SubElement(library_descriptor, 'LIBRARY_NAME')
        library_name.text = self._get_library_name(sample_name)

        library_strategy = ET.SubElement(library_descriptor,
                                         "LIBRARY_STRATEGY")
        library_strategy.text = self.library_strategy
        library_source = ET.SubElement(library_descriptor,
                                       "LIBRARY_SOURCE")
        library_source.text = self.library_source
        library_selection = ET.SubElement(library_descriptor,
                                          "LIBRARY_SELECTION")
        library_selection.text = self.library_selection
        library_layout = ET.SubElement(library_descriptor,
                                       "LIBRARY_LAYOUT")
        ET.SubElement(library_layout, "SINGLE")
        library_construction_protocol_element = ET.SubElement(
            library_descriptor, "LIBRARY_CONSTRUCTION_PROTOCOL")
        library_construction_protocol_element.text = escape(clean_whitespace(
            library_construction_protocol))

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
        xml.etree.Element
            The root elelement of the generated ``ElementTree``
        """
        study_alias = self._get_study_alias()
        experiment_set = ET.Element('EXPERIMENT_SET', {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "ftp://ftp.sra.ebi.ac.uk/meta/xsd"
                                             "/sra_1_3/SRA.experiment.xsd"})
        for sample_name, sample_info in sorted(self.samples.items()):
            sample_alias = self._get_sample_alias(sample_name)

            experiment_alias = self._get_experiment_alias(sample_name)

            platform = sample_info['prep']['platform']
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
            design_description.text = escape(clean_whitespace(
                sample_info['prep']['experiment_design_description']))
            ET.SubElement(
                design, 'SAMPLE_DESCRIPTOR', {'refname': sample_alias}
            )

            self._generate_library_descriptor(
                design, sample_name,
                sample_info['prep']['library_construction_protocol']
            )

            self._generate_spot_descriptor(design, platform)

            platform_element = ET.SubElement(experiment, 'PLATFORM')
            platform_info = ET.SubElement(platform_element,
                                          platform.upper())
            instrument_model = ET.SubElement(platform_info,
                                             'INSTRUMENT_MODEL')
            instrument_model.text = 'unspecified'

            if sample_info['prep']:
                experiment_attributes = ET.SubElement(
                    experiment, 'EXPERIMENT_ATTRIBUTES')
                self._add_dict_as_tags_and_values(experiment_attributes,
                                                  'EXPERIMENT_ATTRIBUTE',
                                                  sample_info['prep'])

        return experiment_set

    def generate_run_xml(self):
        """Generates the run XML file

        Returns
        -------
        xml.etree.Element
            The root elelement of the generated ``ElementTree``
        """
        run_set = ET.Element('RUN_SET', {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "ftp://ftp.sra.ebi.ac.uk/meta/xsd"
                                             "/sra_1_3/SRA.run.xsd"})
        for sample_name, sample_info in sorted(viewitems(self.samples)):

            experiment_alias = self._get_experiment_alias(sample_name)

            file_type = sample_info['prep']['file_type']
            file_path = sample_info['prep']['file_path']

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
                'filename': join(self.ebi_dir, basename(file_path)),
                'filetype': file_type,
                'quality_scoring_system': 'phred',
                'checksum_method': 'MD5',
                'checksum': md5}
            )

        return run_set

    def generate_submission_xml(self, action):
        """Generates the submission XML file

        Parameters
        ----------
        action : {'ADD', 'VALIDATE', 'UPDATE'}
            What action to take when communicating with EBI

        Returns
        -------
        xml.etree.Element
            The root elelement of the generated ``ElementTree``

        Raises
        ------
        NoXMLError
            If one of the necessary XML files has not been generated
        """
        if any([self.study_xml_fp is None,
                self.sample_xml_fp is None,
                self.experiment_xml_fp is None,
                self.run_xml_fp is None]):
            raise NoXMLError("One of the necessary XML files has not been "
                             "generated. Make sure you write out the other "
                             "XML files before attempting to write the "
                             "submission XML file.")

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
        ET.SubElement(study_action, action, {
            'schema': 'study',
            'source': basename(self.study_xml_fp)}
        )

        sample_action = ET.SubElement(actions, 'ACTION')
        ET.SubElement(sample_action, action, {
            'schema': 'sample',
            'source': basename(self.sample_xml_fp)}
        )

        experiment_action = ET.SubElement(actions, 'ACTION')
        ET.SubElement(experiment_action, action, {
            'schema': 'experiment',
            'source': basename(self.experiment_xml_fp)}
        )

        run_action = ET.SubElement(actions, 'ACTION')
        ET.SubElement(run_action, action, {
            'schema': 'run', 'source': basename(self.run_xml_fp)}
        )

        if action == 'ADD':
            hold_action = ET.SubElement(actions, 'ACTION')
            ET.SubElement(hold_action, 'HOLD', {
                'HoldUntilDate': str(date.today() + timedelta(365))}
            )

        return submission_set

    def _write_xml_file(self, xml_gen_fn, attribute_name, fp,
                        xml_gen_fn_arg=None):
        """Writes an XML file after calling one of the XML generation
        functions

        Parameters
        ----------
        xml_gen_fn : function
            The function that will be called to generate the XML that will be
            written
        attribute_name : str
            The name of the attribute in which to store the output filepath
        fp : str
            The filepath to which the XML will be written
        xml_gen_fn_arg : str, optional
            Defaults to None. If None, no arguments will be passed to
            xml_gen_fn. Otherwise, this will be passed as the only argument to
            xml_gen_fn

        Notes
        -----
        xml_gen_fn_arg is needed for generating the submission XML
        """
        if xml_gen_fn_arg is None:
            xml_element = xml_gen_fn()
        else:
            xml_element = xml_gen_fn(xml_gen_fn_arg)

        xml = minidom.parseString(ET.tostring(xml_element))

        with open(fp, 'w') as outfile:
            outfile.write(xml.toxml(encoding='UTF-8'))

        setattr(self, attribute_name, fp)

    def write_study_xml(self, fp):
        """Write the study XML file using the current data

        Parameters
        ----------
        fp : str
            The filepath to which the XML will be written

        Notes
        -----
        If `fp` points to an existing file, it will be overwritten
        """
        self._write_xml_file(self.generate_study_xml, 'study_xml_fp', fp)

    def write_sample_xml(self, fp):
        """Write the sample XML file using the current data

        Parameters
        ----------
        fp : str
            The filepath to which the XML will be written

        Notes
        -----
        If `fp` points to an existing file, it will be overwritten
        """
        self._write_xml_file(self.generate_sample_xml, 'sample_xml_fp', fp)

    def write_experiment_xml(self, fp):
        """Write the experiment XML file using the current data

        Parameters
        ----------
        fp : str
            The filepath to which the XML will be written

        Notes
        -----
        If `fp` points to an existing file, it will be overwritten
        """
        self._write_xml_file(self.generate_experiment_xml,
                             'experiment_xml_fp', fp)

    def write_run_xml(self, fp):
        """Write the run XML file using the current data

        Parameters
        ----------
        fp : str
            The filepath to which the XML will be written

        Notes
        -----
        If `fp` points to an existing file, it will be overwritten
        """
        self._write_xml_file(self.generate_run_xml, 'run_xml_fp', fp)

    def write_submission_xml(self, fp, action):
        """Write the submission XML file using the current data

        Parameters
        ----------
        fp : str
            The filepath to which the XML will be written
        action : {'ADD', 'VALIDATE', 'UPDATE'}
            What action to take when communicating with EBI

        Notes
        -----
        If `fp` points to an existing file, it will be overwritten
        """
        self._write_xml_file(self.generate_submission_xml, 'submission_xml_fp',
                             fp, action)

    def write_all_xml_files(self, study_fp, sample_fp, experiment_fp, run_fp,
                            submission_fp, action):
        """Write all XML files needed for an EBI submission using current data

        Parameters
        ----------
        study_fp : str
            The filepath to which the study XML will be written
        sample_fp : str
            The filepath to which the sample XML will be written
        experiment_fp : str
            The filepath to which the experiment XML will be written
        run_fp : str
            The filepath to which the run XML will be written
        submission_fp : str
            The filepath to which the submission XML will be written
        action : {'ADD', 'VALIDATE', 'UPDATE'}
            What action to take when communicating with EBI

        Notes
        -----
        If any of the filepaths point to an existing file, it will be
        overwritten
        """
        self.write_study_xml(study_fp)
        self.write_sample_xml(sample_fp)
        self.write_experiment_xml(experiment_fp)
        self.write_run_xml(run_fp)
        self.write_submission_xml(submission_fp, action)

    def add_samples_from_templates(self, sample_template, prep_template,
                                   per_sample_fastq_dir):
        """
        Parameters
        ----------
        sample_template : file
        prep_template : file
        per_sample_fastq_dir : str
            Path to the directory containing per-sample FASTQ files where
            the sequence labels should be:
            ``SampleID_SequenceNumber And Additional Notes if Applicable``

        Raises
        ------
        EBISumbissionError
            If a sample doesn't have the required EBI submission information
        """
        if not exists(per_sample_fastq_dir):
            raise IOError('The directory with the FASTQ file does not exist.')

        for sample in iter_file_via_list_of_dicts(sample_template):
            sample_name = sample.pop('sample_name')
            taxon_id = sample.pop('taxon_id', None)
            scientific_name = sample.pop('scientific_name', None)
            description = sample.pop('description', None)

            if taxon_id is None or scientific_name is None or \
                    description is None:
                raise EBISumbissionError(
                    "Sample '%s' is missing required EBI submission "
                    "information. taxon_id: %s; scientific_name: %s; "
                    "description: %s" % (sample_name, taxon_id,
                                         scientific_name, description))

            self.add_sample(sample_name, taxon_id, scientific_name,
                            description, **sample)

        prep_template_samples = []
        for prep in iter_file_via_list_of_dicts(prep_template):
            sample_name = prep.pop('sample_name')
            prep_template_samples.append(sample_name)
            platform = prep.pop('platform')
            experiment_design_description = prep.pop(
                'experiment_design_description')
            library_construction_protocol = prep.pop(
                'library_construction_protocol')

            file_path = join(per_sample_fastq_dir, sample_name+'.fastq.gz')
            self.add_sample_prep(sample_name, platform, 'fastq',
                                 file_path, experiment_design_description,
                                 library_construction_protocol,
                                 **prep)

        to_remove = set(self.samples).difference(prep_template_samples)
        for sample in to_remove:
            del self.samples[sample]

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
        if any([self.study_xml_fp is None,
                self.sample_xml_fp is None,
                self.experiment_xml_fp is None,
                self.run_xml_fp is None,
                self.submission_xml_fp is None]):
            raise NoXMLError("One of the necessary XML files has not been "
                             "generated. Make sure you write out all 5 of the "
                             "XML files before attempting to generate the "
                             "curl command.")

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
