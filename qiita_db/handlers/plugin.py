# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import HTTPError

from .oauth2 import OauthBaseHandler, authenticate_oauth
import qiita_db as qdb


def _get_plugin(name, version):
    """Returns the plugin with the given name and version

    Parameters
    ----------
    name : str
        The name of the plugin
    version : str
        The version of the plugin

    Returns
    -------
    qiita_db.software.Software
        The requested plugin

    Raises
    ------
    HTTPError
        If the plugin does not exist, with error code 404
        If there is a problem instantiating the plugin, with error code 500
    """
    try:
        plugin = qdb.software.Software.from_name_and_version(name, version)
    except qdb.exceptions.QiitaDBUnknownIDError:
        raise HTTPError(404)
    except Exception as e:
        raise HTTPError(500, 'Error instantiating plugin %s %s: %s'
                        % (name, version, str(e)))

    return plugin


class PluginHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, name, version):
        with qdb.sql_connection.TRN:
            plugin = _get_plugin(name, version)
            response = {
                'name': plugin.name,
                'version': plugin.version,
                'description': plugin.description,
                'commands': [c.name for c in plugin.commands],
                'publications': [{'DOI': doi, 'PubMed': pubmed}
                                 for doi, pubmed in plugin.publications],
                'default_workflows': [w.name
                                      for w in plugin.default_workflows],
                'type': plugin.type,
                'active': plugin.active}
        self.write(response)


class CommandHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self):
        """Creates a new command in the system"""
        pass
