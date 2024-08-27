"""Sphinx configuration should be added to pyproject.toml.

This file just reads the settings via the `sphinx-pyproject` package.
"""

from sphinx_pyproject import SphinxConfig

from cavendish_particle_tracks import __version__ as cpt_version

config = SphinxConfig(
    "../pyproject.toml",
    globalns=globals(),
    config_overrides={"version": cpt_version},
)
