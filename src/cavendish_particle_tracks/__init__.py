try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._main_widget import ParticleTracksWidget

__all__ = ("ParticleTracksWidget",)
