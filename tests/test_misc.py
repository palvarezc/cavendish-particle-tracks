import importlib
import sys
import pytest



def test_version_fallback(mocker):
    """Test the versioning fallback (in case setuptools_scm didn't work)"""
    import cavendish_particle_tracks  # fmt: skip

    assert cavendish_particle_tracks.__version__ != "unknown"  # type: ignore[attr-defined]

    mocker.patch.dict(
        sys.modules, {"cavendish_particle_tracks._version": None}
    )
    importlib.reload(cavendish_particle_tracks)
    assert cavendish_particle_tracks.__version__ == "unknown"  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "image_filename",
    ["tests/data/View_1.tiff", "tests/data/View_2.tiff"],
)
def test_smoke_open_test_image(make_napari_viewer, image_filename):
    """Test that we can open the test images in napari"""
    viewer = make_napari_viewer()
    viewer.open(image_filename)
    viewer.close()
