# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from future import standard_library
from os.path import join, dirname, abspath

from qiita_core.exceptions import MissingConfigSection
from qiita_core.qiita_settings import qiita_config

with standard_library.hooks():
    from configparser import ConfigParser


class PortalStyleManager(object):
    """Holds the portal style information

    Parameters
    ----------
    conf_fp: str, optional
        Filepath to the configuration file. Default: portal.txt

    Attributes
    ----------
    logo : str
        Path from base URL to the site logo
    title : str
        Site title
    index header : str
        Welcome text header for the website
    index_text : str
        Welcome text for the website
    example_search : str
        Example search to be shown on the study listing page
    custom_css : str
        custom CSS for the portal
    conf_fp : str
        The filepath to the portal styling config file
    css_fp : str
        The filepath to the portal styling custom CSS
    """
    def __init__(self):
        if qiita_config.portal_fp:
            self.conf_fp = qiita_config.portal_fp
        else:
            self.conf_fp = join(dirname(abspath(__file__)),
                                'support_files/config_portal.cfg')

        # Parse the configuration file
        config = ConfigParser()
        with open(self.conf_fp, 'U') as conf_file:
            config.readfp(conf_file)

        _required_sections = {'sitebase', 'index', 'study_list'}
        if not _required_sections.issubset(set(config.sections())):
            missing = _required_sections - set(config.sections())
            raise MissingConfigSection(', '.join(missing))

        self.css_fp = config.get('sitebase', 'CSS_FP')
        # Load the custom CSS if needed
        self.custom_css = ''
        if self.css_fp:
            with open(self.css_fp, 'U') as f:
                self.custom_css = f.read()

        self._get_sitebase(config)
        self._get_index(config)
        self._get_study_list(config)

    def _get_sitebase(self, config):
        """Get the configuration of the sitebase section"""
        self.logo = config.get('sitebase', 'LOGO')
        self.title = config.get('sitebase', 'TITLE')

    def _get_index(self, config):
        """Get the configuration of the index section"""
        self.index_header = config.get('index', 'HEADER')
        self.index_text = config.get('index', 'TEXT')

    def _get_study_list(self, config):
        """Get the configuration of the study_list section"""
        self.example_search = config.get('study_list', 'EXAMPLE_SEARCH')


portal_styling = PortalStyleManager()
