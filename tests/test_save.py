from glob import glob
from os import chdir, stat


def test_cant_save_empty(cpt_widget, capsys):
    # click the save button
    cpt_widget._on_click_save()

    # check we see the error info
    captured = capsys.readouterr()
    assert "No data to be saved" in captured.out


def test_save_single_particle(cpt_widget, tmp_path):
    chdir(tmp_path)  # change to the tmp_path

    # start napari and the particle widget, add a single particle
    cpt_widget.particle_decays_menu.setCurrentIndex(1)  # select the Σ
    assert len(cpt_widget.data) == 1, "Expecting one particle in the table"

    # click the save button
    cpt_widget._on_click_save()

    # check we have a csv file
    csv_files = glob("./*.csv")
    assert len(csv_files) == 1, "No csv file found"
    assert stat(csv_files[0]).st_size != 0, "File is empty"
