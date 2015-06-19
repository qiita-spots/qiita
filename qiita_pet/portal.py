# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from os import environ
from os.path import dirname, abspath, join
from future import standard_library

from qiita_core.exceptions import MissingConfigSection

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
    navbar_color : str
        Hex or text color for navbar background color
    navbar_highlight : str
        Hex or text color for navbar highlight of selected menu
    navbar_text_color : str
        Hex or text color for navbar menu text
    navbar_text_hover : str
        Hex or text color for navbar hover over for menu text
    text_bg : str
        Hex or text color for index jumbotron background
    text_color : str
        Hex or text color for index welcome text
    index header : str
        Welcome text header for the website
    index_text : str
        Welcome text for the website
    example_search : str
        Example search to be shown on the study listing page
    """
    def __init__(self, conf_fp=None):
        # If conf_fp is None, we default to the test configuration file
        try:
            conf_fp = environ['QIITA_PORTAL_FP']
        except KeyError:
            conf_fp = join(dirname(abspath(__file__)),
                           'support_files/portal.txt')
        self.conf_fp = conf_fp

        # Parse the configuration file
        config = ConfigParser()
        with open(conf_fp, 'U') as conf_file:
            config.readfp(conf_file)

        _required_sections = {'sitebase', 'index', 'study_list'}
        if not _required_sections.issubset(set(config.sections())):
            missing = _required_sections - set(config.sections())
            raise MissingConfigSection(', '.join(missing))

        self._get_sitebase(config)
        self._get_index(config)
        self._get_study_list(config)

    def _get_sitebase(self, config):
        """Get the configuration of the sitebase section"""
        self.logo = config.get('sitebase', 'LOGO')
        self.title = config.get('sitebase', 'TITLE')
        self.navbar_color = config.get('sitebase', 'NAVBAR_COLOR')
        self.navbar_highlight = config.get('sitebase', 'NAVBAR_HIGHLIGHT')
        self.navbar_text_color = config.get('sitebase', 'NAVBAR_TEXT_COLOR')
        self.navbar_text_hover = config.get('sitebase', 'NAVBAR_TEXT_HOVER')

    def _get_index(self, config):
        """Get the configuration of the index section"""
        self.text_bg = config.get('index', 'TEXT_BG')
        self.text_color = config.get('index', 'TEXT_COLOR')
        self.index_header = config.get('index', 'HEADER')
        self.index_text = config.get('index', 'TEXT')

    def _get_study_list(self, config):
        """Get the configuration of the study_list section"""
        self.example_search = config.get('study_list', 'EXAMPLE_SEARCH')

portal_styling = PortalStyleManager()
