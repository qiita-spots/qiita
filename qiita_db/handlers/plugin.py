# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads
from glob import glob
from os.path import join

from tornado.web import HTTPError

from .oauth2 import OauthBaseHandler, authenticate_oauth2
from qiita_core.qiita_settings import qiita_config
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
        raise HTTPError(500, reason='Error instantiating plugin %s %s: %s'
                        % (name, version, str(e)))

    return plugin


class PluginHandler(OauthBaseHandler):
    @authenticate_oauth2(default_public=False, inject_user=False)
    def get(self, name, version):
        """Retrieve the plugin information

        Parameters
        ----------
        name : str
            The plugin name
        version : str
            The plugin version

        Returns
        -------
        dict
            The plugin information:
            'name': the plugin name
            'version': the plugin version
            'description': the plugin description
            'commands': list of the plugin commands
            'publications': list of publications
            'default_workflows': list of the plugin default workflows
            'type': the plugin type
            'active': whether the plugin is active or not
        """
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


class CommandListHandler(OauthBaseHandler):
    @authenticate_oauth2(default_public=False, inject_user=False)
    def post(self, name, version):
        """Create new command for a plugin

        Parameters
        ----------
        name : str
            The name of the plugin
        version : str
            The version of the plugin
        """
        with qdb.sql_connection.TRN:
            plugin = _get_plugin(name, version)

            cmd_name = self.get_argument('name')
            cmd_desc = self.get_argument('description')
            req_params = loads(self.get_argument('required_parameters'))
            opt_params = loads(self.get_argument('optional_parameters'))

            for p_name, vals in opt_params.items():
                if vals[0].startswith('mchoice'):
                    opt_params[p_name] = [vals[0], loads(vals[1])]
                    if len(vals) == 2:
                        opt_params[p_name] = [vals[0], loads(vals[1])]
                    elif len(vals) == 4:
                        opt_params[p_name] = [vals[0], loads(vals[1]), vals[2],
                                              vals[3]]
                    else:
                        raise qdb.exceptions.QiitaDBError(
                            "Malformed parameters dictionary, the format "
                            "should be either {param_name: [parameter_type, "
                            "default]} or {parameter_name: (parameter_type, "
                            "default, name_order, check_biom_merge)}. Found: "
                            "%s for parameter name %s"
                            % (vals, p_name))

            outputs = self.get_argument('outputs', None)
            if outputs:
                outputs = loads(outputs)
            dflt_param_set = loads(self.get_argument('default_parameter_sets'))
            analysis_only = self.get_argument('analysis_only', False)

            parameters = req_params
            parameters.update(opt_params)

            cmd = qdb.software.Command.create(
                plugin, cmd_name, cmd_desc, parameters, outputs,
                analysis_only=analysis_only)

            if dflt_param_set is not None:
                for name, vals in dflt_param_set.items():
                    qdb.software.DefaultParameters.create(name, cmd, **vals)

        self.finish()


def _get_command(plugin_name, plugin_version, cmd_name):
    """Returns the command with the given name within the given plugin

    Parameters
    ----------
    plugin_name : str
        The name of the plugin
    plugin_version : str
        The version of the plugin
    cmd_name : str
        The name of the command in the plugin

    Returns
    -------
    qiita_db.software.Command
        The requested command

    Raises
    ------
    HTTPError
        If the command does not exist, with error code 404
        If there is a problem instantiating the command, with error code 500
    """
    plugin = _get_plugin(plugin_name, plugin_version)
    try:
        cmd = plugin.get_command(cmd_name)
    except qdb.exceptions.QiitaDBUnknownIDError:
        raise HTTPError(404)
    except Exception as e:
        raise HTTPError(500, reason='Error instantiating cmd %s of plugin '
                        '%s %s: %s' % (cmd_name, plugin_name,
                                       plugin_version, str(e)))

    return cmd


class CommandHandler(OauthBaseHandler):
    @authenticate_oauth2(default_public=False, inject_user=False)
    def get(self, plugin_name, plugin_version, cmd_name):
        """Retrieve the command information

        Parameters
        ----------
        plugin_name : str
            The plugin name
        plugin_version : str
            The plugin version
        cmd_name : str
            The command name

        Returns
        -------
        dict
            The command information
            'name': the command name
            'description': the command description
            'required_parameters': dict with the required parameters, in the
                format {parameter_name: [type, [subtypes]]}
            'optional_parameters': dict with the optional parameters, in the
                format {parameter_name: [type, default value]}
            'default_parameter_sets': dict with the default parameter sets, in
                the format {parameter set name: {parameter_name: value}}
        """
        with qdb.sql_connection.TRN:
            cmd = _get_command(plugin_name, plugin_version, cmd_name)
            response = {
                'name': cmd.name,
                'description': cmd.description,
                'required_parameters': cmd.required_parameters,
                'optional_parameters': cmd.optional_parameters,
                'default_parameter_sets': {
                    p.name: p.values for p in cmd.default_parameter_sets}}
        self.write(response)


class CommandActivateHandler(OauthBaseHandler):
    @authenticate_oauth2(default_public=False, inject_user=False)
    def post(self, plugin_name, plugin_version, cmd_name):
        """Activates the command

        Parameters
        ----------
        plugin_name : str
            The plugin name
        plugin_version : str
            The plugin version
        cmd_name : str
            The command name
        """
        with qdb.sql_connection.TRN:
            cmd = _get_command(plugin_name, plugin_version, cmd_name)
            cmd.activate()

        self.finish()


class ReloadPluginAPItestHandler(OauthBaseHandler):
    @authenticate_oauth2(default_public=False, inject_user=False)
    def post(self):
        """Reloads the plugins"""
        conf_files = glob(join(qiita_config.plugin_dir, "*.conf"))
        for fp in conf_files:
            s = qdb.software.Software.from_file(fp, update=True)
            s.activate()
            s.register_commands()

        self.finish()
