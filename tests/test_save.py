from glob import glob
from os import stat

import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialogButtonBox, QLineEdit, QMessageBox

from .conftest import get_dialog


def test_cant_save_empty(cpt_widget, capsys):
    # click the save button
    cpt_widget._on_click_save()

    # check we see the error info
    captured = capsys.readouterr()
    assert "There is no data in the table to save." in captured.out


@pytest.mark.parametrize(
    "file_name, expect_data_loaded",
    [
        ("my_file.csv", True),
        ("my_file.pdf", False),
    ],
)
def test_save_single_particle(
    cpt_widget, tmp_path, qtbot: QtBot, file_name, expect_data_loaded
):

    # start napari and the particle widget, add a single particle
    cpt_widget.cmb_add_particle.setCurrentIndex(1)  # select the Σ
    assert len(cpt_widget.data) == 1, "Expecting one particle in the table"

    def set_filename_and_close(dialog):
        qtbot.addWidget(dialog)
        dialog.setDirectory(str(tmp_path))
        dialog.findChild(QLineEdit, "fileNameEdit").setText(file_name)
        buttonbox = dialog.findChild(QDialogButtonBox, "buttonBox")
        openbutton = buttonbox.children()[1]
        qtbot.mouseClick(openbutton, Qt.LeftButton, delay=1)

    # Open and retrieve file dialog
    get_dialog(
        dialog_trigger=cpt_widget._on_click_save,
        dialog_action=set_filename_and_close,
        time_out=5,
    )

    if expect_data_loaded:
        # check we have a csv file
        csv_files = glob(str(tmp_path / "*.csv"))
        assert len(csv_files) == 1, "No csv file found"
        assert stat(csv_files[0]).st_size != 0, "File is empty"
    else:
        msgbox = cpt_widget.msg
        assert isinstance(msgbox, QMessageBox)
        assert msgbox.icon() == QMessageBox.Warning
        assert msgbox.text() == (
            "The file must be a CSV file. Please try again."
        )
