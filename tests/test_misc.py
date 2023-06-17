import importlib
import sys


def test_version_fallback(mocker):
    """Test the versioning fallback (in case setuptools_scm didn't work)"""
    import cavendish_particle_tracks  # fmt: skip
    assert cavendish_particle_tracks.__version__ != "unknown"  # type: ignore[attr-defined]

    mocker.patch.dict(
        sys.modules, {"cavendish_particle_tracks._version": None}
    )
    importlib.reload(cavendish_particle_tracks)
    assert cavendish_particle_tracks.__version__ == "unknown"  # type: ignore[attr-defined]
