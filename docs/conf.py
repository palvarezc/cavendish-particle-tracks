from cavendish_particle_tracks import __version__ as cpt_version
from sphinx_pyproject import SphinxConfig

config = SphinxConfig(
    "../pyproject.toml",
    globalns=globals(),
    config_overrides={"version": cpt_version},
)
