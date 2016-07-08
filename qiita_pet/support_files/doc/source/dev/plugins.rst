.. _plugins:

.. index :: plugins

Plugins
=======

Qiita plugins allow to extend the functionality of Qiita by adding new data
formats and/or new processing pipelines. The list of officially supported
plugins can be found in the `Qiita Spots <https://github.com/qiita-spots>`__
GitHub organization.

Overview of Qiita's plugin system
---------------------------------

Qiita's plugin system has been designed to increase Qiita's flexibility to
process -omics datasets, while allowing plugin developers to create plugins
using the programming language that they are more comfortable with.

In order to achieve this flexibility, Qiita represents the different -omics
datasets using ``Artifacts``. An ``Artifact`` is a file or set of files that
conceptually represents a dataset. However, Qiita does not understand the
contents of the artifact, so it doesn't know to show information about the
artifact or which pipelines/methods can be applied to it. It is up to the Qiita
plugins to define what an artifact is and which methods can be applied to it.
With the goal of reducing community development effort, there are two different
types of plugins: ``Qiita Type Plugins`` and ``Qiita Plugins``.

The ``Qiita Type Plugins`` define new artifact types. These plugins must define
two operations: ``Validate`` and ``Generate HTML summary``.

Given the artifact type, the prep information and the user-uploaded files, the
``Validate`` operation decides if the user-uploaded files creates a valid
artifact of the given type. If the files do not create a valid artifact, the
plugin should try to fix the files using the given information, but only if the
files can be deterministically fixed and not generate ambiguous results.

The ``Generate HTML summary`` generates a single HTML file with an overview
of the contents of the artifact. The only limitation on this HTML is that all
the images and libraries used in the HTML files should be embedded in a single
HTML file.

The ``Qiita Plugins`` define pipelines and methods that can be applied to
the artifacts. They do not directly depend on the ``Qiita Type Plugins``,
although the may depend on a given ``Qiita Type Plugin`` being available in the
system. There are no limitation on the ``Qiita Plugin`` methods: they can take
one or more input artifacts and generate one or more output artifacts. Besides
defining individual methods, the ``Qiita Plugins`` also have the ability to
define default ``workflows``, where a ``workflow`` is a set of methods connected
by their input/outputs to perform a bigger task over one or a set of artifacts.

The goal of having the ``Qiita Type Plugins`` independent of the
``Qiita Plugins`` is that other plugin developers will be able to rely on
previously defined types to develop their own pipelines.

Plugins run in independent environments from Qiita, allowing them to have any
dependency stack as well as being able to be written in any language. Qiita only
needs a single script to start the plugin, which should follow this signature:

.. code-block:: bash

    start_script_name QIITA_SERVER_URL JOB_ID OUTPUT_DIR

The plugin will then use QIITA's REST API to gather the needed information
to run the given job ``JOB_ID`` and to send back the results of the job.

Developing a Qiita Plugin
-------------------------

To facilitate the development of Qiita Plugins, we have created a library that
simplifies the usage of Qiita's REST api:
`Qiita Client <https://github.com/qiita-spots/qiita_client>`__. This library
encapsulates the authentication of the plugin when using Qiita's REST api as
well as providing convenient functions to retrieve the job information, update
the job status and complete the job.

We have also created two `Cookiecutter <https://github.com/audreyr/cookiecutter>`__
templates to create plugins:

- `qtp-template-cookiecutter <https://github.com/qiita-spots/qtp-template-cookiecutter>`__: Template to create Qiita Type Plugins
- `qp-template-cookiecutter <https://github.com/qiita-spots/qp-template-cookiecutter>`__: Template to create Qiita Plugins
