import csv
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
        ("my_file.pkl", True),
        ("my_file.pdf", False),
    ],
)
def test_save_single_particle(
    cpt_widget, tmp_path, qtbot: QtBot, file_name, expect_data_loaded
):
    # start napari and the particle widget, add a single particle
    cpt_widget.particle_decays_menu.setCurrentIndex(1)  # select the Σ
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
        expected_file_name = file_name  # Expect the file name to be the one we set
        csv_files = glob(str(tmp_path / "*.csv"))
        pkl_files = glob(str(tmp_path / "*.pkl"))

        expect_a_csv_and_have_one = (
            expected_file_name.endswith(".csv") and len(csv_files) == 1
        )
        expect_a_pkl_and_have_one = (
            expected_file_name.endswith(".pkl") and len(pkl_files) == 1
        )
        assert (
            expect_a_csv_and_have_one or expect_a_pkl_and_have_one
        ), "Unexpected number of data files found"

        # Only one file if we've passed the above XOR check
        saved_file = (csv_files + pkl_files)[0]
        assert saved_file.endswith(
            expected_file_name
        ), f"File name {saved_file} does not match expected name: {expected_file_name}"

        saved_file_is_not_empty = stat(saved_file).st_size != 0
        assert saved_file_is_not_empty, f"File {saved_file} is empty"
    else:
        msgbox = cpt_widget.msg
        assert isinstance(msgbox, QMessageBox)
        assert msgbox.icon() == QMessageBox.Warning
        assert msgbox.text() == (
            "The file must be a CSV (*.csv) or Pickle (*.pkl) file. Please try again."
        )


def _assert_file_contents_the_same(left: str, right: str) -> None:
    # Can't use filecmp.cmp because file created on macOS/linux has different line endings to Windows.
    with open(left, encoding="utf8") as f:
        left_contents = f.read()
    with open(right, encoding="utf8") as f:
        right_contents = f.read()
    assert left_contents == right_contents, "File contents are not the same"


def test_csv_file_has_correct_columns(cpt_widget, tmp_path, qtbot: QtBot):
    # start napari and the particle widget, add a single particle
    cpt_widget.particle_decays_menu.setCurrentIndex(4)  # select the Λ
    assert len(cpt_widget.data) == 1, "Expecting one particle in the table"

    file_name = "test_saved_file.csv"

    def set_filename_and_close(dialog):
        # Function of the signature needed to use as a dialog action.
        # Defined internally so we can access the fixtures without passing.
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

    # Check the file has the correct columns
    csv_files = glob(str(tmp_path / "*.csv"))
    assert len(csv_files) == 1, "Expecting one CSV file to be saved"
    with open(csv_files[0], encoding="utf8") as f:
        myreader = csv.reader(f, delimiter=",")
        for row in myreader:
            assert len(row) == 18, "Expecting 18 columns in the CSV file"

    _assert_file_contents_the_same(csv_files[0], "tests/data/test_output_file.csv")
