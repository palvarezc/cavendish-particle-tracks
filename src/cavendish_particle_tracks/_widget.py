"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

import glob

import dask.array
import napari
import numpy as np
from dask_image.imread import imread
from qtpy.QtCore import QPoint
from qtpy.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ._analysis import (
    EXPECTED_PARTICLES,
    VIEW_NAMES,
    NewParticle,
)
from ._calculate import length, radius
from ._decay_angles_dialog import DecayAnglesDialog
from ._magnification_dialog import MagnificationDialog
from ._stereoshift_dialog import StereoshiftDialog


class ParticleTracksWidget(QWidget):
    """Widget containing a simple table of points and track radii per image."""

    layer_measurements: napari.layers.Points

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__()
        self.viewer = napari_viewer
        # define QtWidgets
        self.load = QPushButton("Load data")
        self.cb = QComboBox()
        self.cb.addItems(EXPECTED_PARTICLES)
        self.cb.setCurrentIndex(0)
        self.cb.currentIndexChanged.connect(self._on_click_new_particle)
        self.rad = QPushButton("Calculate radius")
        delete_particle = QPushButton("Delete particle")
        self.lgth = QPushButton("Calculate length")
        self.ang = QPushButton("Calculate decay angles")
        self.stsh = QPushButton("Stereoshift")
        self.mag = QPushButton("Magnification")
        save = QPushButton("Save")

        # setup particle table
        self.table = self._set_up_table()
        self._set_table_visible_vars(False)
        self.table.selectionModel().selectionChanged.connect(
            self._on_row_selection_changed
        )

        # Apply magnification disabled until the magnification parameters are computed
        self.cal = QRadioButton("Apply magnification")
        self.cal.setEnabled(False)

        # connect callbacks
        self.load.clicked.connect(self._on_click_load_data)
        delete_particle.clicked.connect(self._on_click_delete_particle)
        self.rad.clicked.connect(self._on_click_radius)
        self.lgth.clicked.connect(self._on_click_length)
        self.ang.clicked.connect(self._on_click_decay_angles)
        self.stsh.clicked.connect(self._on_click_stereoshift)
        self.cal.toggled.connect(self._on_click_apply_magnification)
        save.clicked.connect(self._on_click_save)

        self.mag.clicked.connect(self._on_click_magnification)
        # TODO: find which of thsese works
        # https://napari.org/stable/gallery/custom_mouse_functions.html
        # self.viewer.mouse_press.callbacks.connect(self._on_mouse_press)
        # self.viewer.events.mouse_press(self._on_mouse_click)

        # layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.load)
        self.layout().addWidget(self.cb)
        self.layout().addWidget(delete_particle)
        self.layout().addWidget(self.rad)
        self.layout().addWidget(self.lgth)
        self.layout().addWidget(self.ang)
        self.layout().addWidget(self.table)
        self.layout().addWidget(self.cal)
        self.layout().addWidget(self.stsh)
        self.layout().addWidget(self.mag)
        self.layout().addWidget(save)

        # disable all calculation buttons
        self.disable_all_buttons()
        # TODO: include self.stsh in the logic, depending on what it actually ends up doing

        # Data analysis
        self.data: list[NewParticle] = []
        # might not need this eventually
        self.mag_a = -1.0e6
        self.mag_b = -1.0e6

    @property
    def camera_center(self):
        # update for 4d implementation as appropriate.
        return (self.viewer.camera.center[1], self.viewer.camera.center[2])

    def _get_selected_points(self, layer_name="Radii and Lengths") -> np.array:
        """Returns array of selected points in the viewer"""

        # Filtering selected layer (layer names are unique)
        points_layers = [
            layer for layer in self.viewer.layers if layer.name == layer_name
        ]
        # Returning selected points in the layer
        selected_points = np.array(
            [points_layers[0].data[i] for i in points_layers[0].selected_data]
        )
        return selected_points

    def _get_selected_row(self) -> np.array:
        """Returns the selected row in the table.

        Note: due to our selection mode only one row selection is possible.
        """
        select = self.table.selectionModel()
        rows = select.selectedRows()
        return rows[0].row()

    def _set_up_table(self) -> QTableWidget:
        """Initial setup of the QTableWidget with one row and columns for each
        point and the calculated radius.
        """
        np = NewParticle()
        self.columns = list(np.__dict__.keys())
        self.columns += ["magnification"]
        self.columns_show_calibrated = np._vars_to_show(True)
        self.columns_show_uncalibrated = np._vars_to_show(False)
        out = QTableWidget(0, len(self.columns))
        out.setHorizontalHeaderLabels(self.columns)
        out.setSelectionBehavior(QAbstractItemView.SelectRows)
        out.setSelectionMode(QAbstractItemView.SingleSelection)
        out.setEditTriggers(QAbstractItemView.NoEditTriggers)
        out.setSelectionBehavior(QTableWidget.SelectRows)
        return out

    def _set_table_visible_vars(self, calibrated) -> None:
        for _ in range(len(self.columns)):
            self.table.setColumnHidden(_, True)
        show = (
            self.columns_show_calibrated
            if calibrated
            else self.columns_show_uncalibrated
        )
        show_index = [
            i for i, item in enumerate(self.columns) if item in set(show)
        ]
        for _ in show_index:
            self.table.setColumnHidden(_, False)

    def _get_table_column_index(self, columntext: str) -> int:
        """Given a column title, return the column index in the table"""
        for i, item in enumerate(self.columns):
            if item == columntext:
                return i

        print("Column ", columntext, " not in the table")
        return -1

    def _on_row_selection_changed(self) -> None:
        """Enable/disable calculation buttons depending on the row selection"""
        try:
            selected_row = self._get_selected_row()
            if self.data[selected_row].index < 4:
                self.rad.setEnabled(True)
                self.lgth.setEnabled(True)
                self.ang.setEnabled(False)
                return
            elif self.data[selected_row].index == 4:
                self.rad.setEnabled(False)
                self.lgth.setEnabled(True)
                self.ang.setEnabled(True)
                return
        except IndexError:
            print("The table is empty.")
        self.disable_all_buttons()

    def disable_all_buttons(self) -> None:
        self.rad.setEnabled(False)
        self.lgth.setEnabled(False)
        self.ang.setEnabled(False)

    def _on_click_radius(self) -> None:
        """When the 'Calculate radius' button is clicked, calculate the radius
        for the currently selected points and assign it to the currently selected table row.
        """

        selected_points = self._get_selected_points()

        # Forcing only 3 points
        if len(selected_points) == 0:
            napari.utils.notifications.show_error(
                "You have not selected any points."
            )
            return
        elif len(selected_points) != 3:
            napari.utils.notifications.show_error(
                "Select three points to calculate the path radius."
            )
            return
        else:
            napari.utils.notifications.show_info(
                f"Adding points to the table: {selected_points}"
            )
        try:
            selected_row = self._get_selected_row()
        except IndexError:
            napari.utils.notifications.show_error(
                "There are no particles in the table."
            )
        else:
            # Assigns the points and radius to the selected row
            for i in range(3):
                point = selected_points[i]
                self.table.setItem(
                    selected_row,
                    self._get_table_column_index("r" + str(i + 1)),
                    QTableWidgetItem(str(point)),
                )

            self.data[selected_row].rpoints = selected_points

            print("calculating radius!")
            rad = radius(*selected_points)

            self.table.setItem(
                selected_row,
                self._get_table_column_index("radius_px"),
                QTableWidgetItem(str(rad)),
            )

            self.data[selected_row].radius_px = rad

            ## Add the calibrated radius to the table
            self.data[selected_row].radius_cm = (
                self.data[selected_row].magnification
                * self.data[selected_row].radius_px
            )
            self.table.setItem(
                selected_row,
                self._get_table_column_index("radius_cm"),
                QTableWidgetItem(str(self.data[selected_row].radius_cm)),
            )

            print("Modified particle ", selected_row)
            print(self.data[selected_row])

    def _on_click_length(self) -> None:
        """When the 'Calculate length' button is clicked, calculate the decay length
        for the currently selected table row.
        """

        selected_points = self._get_selected_points()

        # Force selection of 2 points
        if len(selected_points) == 0:
            napari.utils.notifications.show_error(
                "You have not selected any points."
            )
            return
        elif len(selected_points) != 2:
            napari.utils.notifications.show_error(
                "Select two points to calculate the decay length."
            )
            return
        else:
            napari.utils.notifications.show_info(
                f"Adding points to the table: {selected_points}"
            )

        # Forcing only 2 points
        if len(selected_points) != 2:
            print("Select (only) two points to calculate the decay length.")
            return

        # Assigns the points and radius to the selected row
        try:
            selected_row = self._get_selected_row()
        except IndexError:
            napari.utils.notifications.show_error(
                "There are no particles in the table."
            )
        else:
            for i in range(2):
                point = selected_points[i]
                self.table.setItem(
                    selected_row,
                    self._get_table_column_index("d" + str(i + 1)),
                    QTableWidgetItem(str(point)),
                )
            self.data[selected_row].dpoints = selected_points

            print("calculating decay length!")
            declen = length(*selected_points)
            self.table.setItem(
                selected_row,
                self._get_table_column_index("decay_length_px"),
                QTableWidgetItem(str(declen)),
            )
            self.data[selected_row].decay_length_px = declen

            ## Add the calibrated decay length to the table
            self.data[selected_row].decay_length_cm = (
                self.data[selected_row].magnification
                * self.data[selected_row].decay_length_px
            )
            self.table.setItem(
                selected_row,
                self._get_table_column_index("decay_length_cm"),
                QTableWidgetItem(str(self.data[selected_row].decay_length_cm)),
            )

            print("Modified particle ", selected_row)
            print(self.data[selected_row])

    def _on_click_decay_angles(self) -> None:
        """When the 'Calculate decay angles' buttong is clicked, open the decay angles dialog"""
        dlg = DecayAnglesDialog(self)
        dlg.show()
        point = QPoint(self.pos().x() + self.width(), self.pos().y())
        dlg.move(point)

    def _on_click_stereoshift(self) -> StereoshiftDialog:
        """When the 'Calculate stereoshift' button is clicked, open stereoshift dialog."""
        dlg = StereoshiftDialog(self)
        dlg.show()
        point = QPoint(self.pos().x() + self.width(), self.pos().y())
        dlg.move(point)
        return dlg

    def _on_click_load_data(self) -> None:
        """When the 'Load data' button is clicked, a dialog opens to select the folder containing the data.
        The folder should contain three subfolders named as variations of 'view1', 'view2' and 'view3', and each subfolder should contain the same number of images.
        The images in each folder are loaded as a stack, and the stack is named according to the subfolder name.
        """
        # setup UI
        test_file_dialog = QFileDialog(self)
        test_file_dialog.setFileMode(QFileDialog.Directory)
        # retrieve image folder
        folder_name = test_file_dialog.getExistingDirectory(
            self,
            "Choose folder",
            "./",
            QFileDialog.DontUseNativeDialog
            | QFileDialog.DontResolveSymlinks
            | QFileDialog.ShowDirsOnly
            | QFileDialog.HideNameFilterDetails,
        )

        if folder_name in {"", None}:
            return

        folder_subdirs = glob.glob(folder_name + "/*/")
        # Checks whether the image folder contains a subdirectory for each view.
        three_subdirectories = len(folder_subdirs) == 3
        # Checks that these subdirectories correspond to event views.
        subdir_names_contain_views = all(
            any(view in name.lower() for name in folder_subdirs)
            for view in VIEW_NAMES
        )
        # Checks that each subdirectory contains the same number of images.
        same_image_count = all(
            len(glob.glob(subdir + "/*"))
            == len(glob.glob(folder_subdirs[0] + "/*"))
            for subdir in folder_subdirs
        )
        # If all checks are passed, load the images where the event number is a
        # new spatial dimension (stack) and the views are layers.
        if not (
            three_subdirectories
            and subdir_names_contain_views
            and same_image_count
        ):
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Warning)
            self.msg.setWindowTitle("Data folder structure error")
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.setText(
                "The data folder must contain three subfolders, one for each view, and each subfolder must contain the same number of images."
            )
            self.msg.show()
            return

        def crop(array):
            # Crops view 1 and 2 to same size as view 3 by removing whitespace
            # on left, as images align on the right.
            # this number is the width of image 3.
            magic_number_smallest_view_pixels = -8377
            return array[:, :, magic_number_smallest_view_pixels:, :]

        stacks = []
        for subdir in folder_subdirs:
            stack: dask.array.Array = imread(subdir + "/*")
            stack = crop(stack)
            stacks.append(stack)

        # Concatenate stacks along new spatial dimension such that we have a view, and event slider
        concatenated_stack = dask.array.stack(stacks, axis=0)
        self.viewer.add_image(concatenated_stack, name="Particle Tracks")
        self.viewer.dims.axis_labels = ("View", "Event", "Y", "X")

        measurement_layer_present = "Radii and Lengths" in self.viewer.layers

        if not measurement_layer_present:
            self.layer_measurements = self.viewer.add_points(
                name="Radii and Lengths",
                size=20,
                border_width=7,
                border_width_is_relative=False,
            )

    def _on_click_new_particle(self) -> None:
        """When the 'New particle' button is clicked, append a new blank row to
        the table and select the first cell ready to recieve the first point.
        """
        if self.cb.currentIndex() < 1:
            return

        # add new particle to data
        np = NewParticle()
        np.Name = self.cb.currentText()
        np.index = self.cb.currentIndex()
        np.magnification_a = self.mag_a
        np.magnification_b = self.mag_b
        self.data += [np]

        # add particle (== new row) to the table and select it
        self.table.insertRow(self.table.rowCount())
        self.table.selectRow(self.table.rowCount() - 1)
        self.table.setItem(
            self.table.rowCount() - 1,
            self._get_table_column_index("index"),
            QTableWidgetItem(np.index),
        )
        self.table.setItem(
            self.table.rowCount() - 1,
            self._get_table_column_index("Name"),
            QTableWidgetItem(np.Name),
        )
        self.table.setItem(
            self.table.rowCount() - 1,
            self._get_table_column_index("magnification"),
            QTableWidgetItem(str(np.magnification)),
        )

        print(self.data[-1])
        self.cb.setCurrentIndex(0)

        # # napari notifications
        # napari.utils.notifications.show_info("I created a new particle")

    def _on_click_delete_particle(self) -> None:
        """Delete particle from table and data"""
        try:
            selected_row = self._get_selected_row()
        except IndexError:
            napari.utils.notifications.show_error(
                "There are no particles in the table."
            )
        else:
            msgBox = QMessageBox()
            msgBox.setText("Deleting selected particle")
            msgBox.setInformativeText("Do you want to continue?")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Cancel)
            ret = msgBox.exec()

            if ret == QMessageBox.Yes:
                del self.data[selected_row]
                self.table.removeRow(selected_row)

    def _on_click_magnification(self) -> MagnificationDialog:
        """When the 'Calculate magnification' button is clicked, open the magnification dialog"""

        dlg = MagnificationDialog(self)
        dlg.show()
        point = QPoint(self.pos().x() + self.width(), self.pos().y())
        dlg.move(point)
        return dlg

    def _propagate_magnification(self, a: float, b: float) -> None:
        """Assigns a and b to the class magnification parameters and to each of the particles in data"""
        self.mag_a = a
        self.mag_b = b
        for particle in self.data:
            particle.magnification_a = a
            particle.magnification_b = b

    def _on_click_apply_magnification(self) -> None:
        """Changes the visualisation of the table to show calibrated values for radius and decay_length"""
        if self.cal.isChecked():
            self._apply_magnification()
        self._set_table_visible_vars(self.cal.isChecked())

    def _apply_magnification(self) -> None:
        """Calculates magnification and calibrated radius and length for each particle in data"""

        for i in range(len(self.data)):
            self.data[i].calibrate()
            self.table.setItem(
                i,
                self._get_table_column_index("magnification"),
                QTableWidgetItem(str(self.data[i].magnification)),
            )
            self.table.setItem(
                i,
                self._get_table_column_index("radius_cm"),
                QTableWidgetItem(str(self.data[i].radius_cm)),
            )
            self.table.setItem(
                i,
                self._get_table_column_index("decay_length_cm"),
                QTableWidgetItem(str(self.data[i].decay_length_cm)),
            )

    def _on_click_save(self) -> None:
        """Save list of particles to csv file.
        When the 'Save' button is clicked, the data is saved to a csv file with the current date and time as the filename.
        """

        if not len(self.data):
            napari.utils.notifications.show_error(
                "There is no data in the table to save."
            )
            print("There is no data in the table to save.")
            return

        # setup UI
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("CSV files (*.csv)")
        file_dialog.setDefaultSuffix("csv")
        # retrieve image folder
        file_name, _ = file_dialog.getSaveFileName(
            self,
            "Save file",
            "./",
            "CSV files (*.csv)",
            "CSV files (*.csv)",
            QFileDialog.DontUseNativeDialog,
        )

        if file_name in {"", None}:
            return

        if not file_name.endswith(".csv"):
            file_name += ".csv"

        if "." in file_name[:-4]:
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Warning)
            self.msg.setWindowTitle("Invalid file type")
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.setText("The file must be a CSV file. Please try again.")
            self.msg.show()
            return

        with open(file_name, "w", encoding="UTF8", newline="") as f:
            # write the header
            f.write(",".join(self.data[0]._vars_to_save()) + "\n")

            # write the data
            f.writelines([particle.to_csv() for particle in self.data])

        napari.utils.notifications.show_info("Data saved to " + file_name)
