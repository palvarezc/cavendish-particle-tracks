from glob import glob
from os import chdir, stat

from cavendish_particle_tracks import ParticleTracksWidget


def test_cant_save_empty(make_napari_viewer, capsys):
    viewer = make_napari_viewer()
    widget = ParticleTracksWidget(viewer)

    # click the save button
    widget._on_click_save()

    # check we see the error info
    captured = capsys.readouterr()
    assert "No data to be saved" in captured.out


def test_save_single_particle(make_napari_viewer, tmp_path):
    chdir(tmp_path)  # change to the tmp_path

    # start napari and the particle widget, add a single particle
    viewer = make_napari_viewer()
    widget = ParticleTracksWidget(viewer)
    widget.cb.setCurrentIndex(1)  # select the Σ
    widget._on_click_new_particle()
    assert len(widget.data) == 1, "Expecting one particle in the table"

    # click the save button
    widget._on_click_save()

    # check we have a csv file
    csv_files = glob("./*.csv")
    assert len(csv_files) == 1, "No csv file found"
    assert stat(csv_files[0]).st_size != 0, "File is empty"
