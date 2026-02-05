# -*- coding: utf-8 -*-

name = 'houdini_deadline_api_submission'

version = '1.0.0'

description = \
    """
    Deadline Submission from Houdini with a single HDA.
    """

authors = [u'Matthias Pichler']

tools = []

plugin_for = ['houdini']

requires = [
    'deadline_api-10',
    'farm_environment-2',
    'houdini-17..22',
    'hal_config-2',
    'hal_naming-3',
    # 'hal_ontrack-0',
    # 'hal_shotgun-1',
    'python-2.7..4'
]

build_requires = []

private_build_requires = [
    'rez_builder-2',
    'setuptools_scm-1.15',
    'sphinx_rtd_theme-0.4',
    'python_embedded'
]

def commands():
    """Set up package."""
    env.PYTHONPATH.prepend(
        "{this.root}/site-packages"
    )  # noqa: F821, E501  # pylint: disable=line-too-long
    env.HOUDINI_PATH.prepend("{this.root}/houdini")  # noqa: F821, E501

uuid = '81288561-82e2-4ff0-8b1c-6244f0aa8fd6'

timestamp = 1662533724

tests = {}

format_version = 2

homepage = 'https://gitlab.rezpipeline.com/internal/houdini_deadline_api_submission'
