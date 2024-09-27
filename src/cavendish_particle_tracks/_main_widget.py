"""
This module contains the main Cavendish Particle Tracks widget.

It's the students' home widget, that contains the table of particle decays, and
the buttons to perform all analysis calculations, and to export (save) the data
for further analysis.
"""

import glob

import dask.array
import napari
import numpy as np
from dask_image.imread import imread
from qtpy.QtCore import QPoint, Qt
from qtpy.QtGui import QFont
from qtpy.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ._analysis import EXPECTED_PARTICLES, VIEW_NAMES, ParticleDecay
from ._calculate import length, radius
from ._decay_angles_dialog import DecayAnglesDialog
from ._magnification_dialog import MagnificationDialog
from ._stereoshift_dialog import StereoshiftDialog


class ParticleTracksWidget(QWidget):
    """Widget containing a simple table of points and track radii per image."""

    layer_measurements: napari.layers.Points

    def __init__(
        self,
        napari_viewer: napari.Viewer,
        bypass_load_screen: bool = False,
        docking_area: str = "right",
        shuffling_seed: int = 1,
    ):
        super().__init__()
        self.viewer: napari.Viewer = napari_viewer
        self.bypass_load_screen = bypass_load_screen
        self.docking_area = docking_area
        if self.docking_area != "bottom":
            self.bypass_load_screen = True
        self.shuffling_seed = shuffling_seed

        # define QtWidgets
        self.load_button = QPushButton("Load data")
        self.particle_decays_menu = QComboBox()
        self.particle_decays_menu.addItems(EXPECTED_PARTICLES)
        self.particle_decays_menu.setCurrentIndex(0)
        self.particle_decays_menu.currentIndexChanged.connect(
            self._on_click_new_particle
        )
        self.radius_button = QPushButton("Calculate radius")
        self.delete_particle = QPushButton("Delete particle")
        self.length_button = QPushButton("Calculate length")
        self.decay_angles_button = QPushButton("Calculate decay angles")
        self.stereoshift_button = QPushButton("Stereoshift")
        self.magnification_button = QPushButton("Magnification")
        self.save_data_button = QPushButton("Save")

        # setup particle table
        self.table = self._set_up_table()
        self._set_table_visible_vars(False)
        self.table.selectionModel().selectionChanged.connect(
            self._on_row_selection_changed
        )
        # Apply magnification disabled until the magnification parameters are computed
        self.apply_magnification_button = QRadioButton("Apply magnification")
        self.apply_magnification_button.setEnabled(False)

        # connect callbacks
        self.load_button.clicked.connect(self._on_click_load_data)
        self.delete_particle.clicked.connect(self._on_click_delete_particle)
        self.radius_button.clicked.connect(self._on_click_radius)
        self.length_button.clicked.connect(self._on_click_length)
        self.decay_angles_button.clicked.connect(self._on_click_decay_angles)
        self.stereoshift_button.clicked.connect(self._on_click_stereoshift)
        self.apply_magnification_button.toggled.connect(
            self._on_click_apply_magnification
        )
        self.save_data_button.clicked.connect(self._on_click_save)

        self.magnification_button.clicked.connect(self._on_click_magnification)
        # TODO: find which of thsese works
        # https://napari.org/stable/gallery/custom_mouse_functions.html
        # self.viewer.mouse_press.callbacks.connect(self._on_mouse_press)
        # self.viewer.events.mouse_press(self._on_mouse_click)

        # layout
        self.intro_text = QLabel(
            r"""
   _____                          _ _     _       _____           _   _      _        _______             _
  / ____|                        | (_)   | |     |  __ \         | | (_)    | |      |__   __|           | |
 | |     __ ___   _____ _ __   __| |_ ___| |__   | |__) |_ _ _ __| |_ _  ___| | ___     | |_ __ __ _  ___| | _____
 | |    / _` \ \ / / _ \ '_ \ / _` | / __| '_ \  |  ___/ _` | '__| __| |/ __| |/ _ \    | | '__/ _` |/ __| |/ / __|
 | |___| (_| |\ V /  __/ | | | (_| | \__ \ | | | | |  | (_| | |  | |_| | (__| |  __/    | | | | (_| | (__|   <\__ \
  \_____\__,_| \_/ \___|_| |_|\__,_|_|___/_| |_| |_|   \__,_|_|   \__|_|\___|_|\___|    |_|_|  \__,_|\___|_|\_\___/

"""
        )
        self.intro_text.setFont(QFont("Lucida Console", 5))
        self.intro_text.setTextFormat(Qt.TextFormat.PlainText)

        if self.docking_area == "bottom":
            self.buttonbox = QGridLayout()
            self.buttonbox.addWidget(self.load_button, 0, 0)
            self.buttonbox.addWidget(self.particle_decays_menu, 1, 0)
            self.buttonbox.addWidget(self.delete_particle, 1, 1)
            self.buttonbox.addWidget(self.radius_button, 2, 0)
            self.buttonbox.addWidget(self.length_button, 2, 1)
            self.buttonbox.addWidget(self.decay_angles_button, 3, 0)
            self.buttonbox.addWidget(self.stereoshift_button, 3, 1)
            self.buttonbox.addWidget(self.magnification_button, 4, 0)
            self.buttonbox.addWidget(self.apply_magnification_button, 4, 1)
            self.buttonbox.addWidget(self.save_data_button, 5, 0)

            layout_outer = QHBoxLayout()
            self.setLayout(layout_outer)
            self.layout().addWidget(self.intro_text)
            layout_outer.addLayout(self.buttonbox)
            self.layout().addWidget(self.table)

        else:
            self.buttonbox = QVBoxLayout()
            self.buttonbox.addWidget(self.load_button)
            self.buttonbox.addWidget(self.particle_decays_menu)
            self.buttonbox.addWidget(self.delete_particle)
            self.buttonbox.addWidget(self.radius_button)
            self.buttonbox.addWidget(self.length_button)
            self.buttonbox.addWidget(self.decay_angles_button)
            self.buttonbox.addWidget(self.table)
            self.buttonbox.addWidget(self.apply_magnification_button)
            self.buttonbox.addWidget(self.stereoshift_button)
            self.buttonbox.addWidget(self.magnification_button)
            self.buttonbox.addWidget(self.save_data_button)
            self.setLayout(self.buttonbox)

        # Disable native napari layer controls - show again on closing this widget (hide).
        # NB: Both of these will break in napari 0.6.0
        self.viewer.window._qt_viewer.layerButtons.hide()
        # Disable viewer buttons, prevents accidental crash due to viewing image stack side on.
        self.viewer.window._qt_viewer.viewerButtons.hide()
        self.set_UI_image_loaded(False, self.bypass_load_screen)
        # TODO: include self.stsh in the logic, depending on what it actually ends up doing

        # Data analysis
        self.data: list[ParticleDecay] = []
        # might not need this eventually
        self.mag_a = -1.0e6
        self.mag_b = -1.0e6

        # Dialog pointers to reuse
        self.mag_dlg: MagnificationDialog | None = None
        self.stereoshift_dlg: StereoshiftDialog | None = None
        self.stereoshift_isopen = False
        self.decay_angles_dlg: DecayAnglesDialog | None = None
        self.decay_angles_isopen = False

        @self.viewer.layers.events.connect
        def _on_layerlist_changed(event):
            """When the layer list changes, update the button availability"""
            self.set_button_availability()

    def hideEvent(self, event):
        """When the widget is 'closed' (napari just hides it), show the layer buttons again.
        If data has been recorded, prompt the user to save it before closing the widget.
        """
        if len(self.data) > 0:
            self._confirm_save_before_closing()
        self.viewer.window._qt_viewer.layerButtons.show()
        self.viewer.window._qt_viewer.viewerButtons.show()
        super().hideEvent(event)

    def _confirm_save_before_closing(self):
        """Prompt the user to save data before closing the widget."""
        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Warning)
        message_box.setText(
            "Closing Cavendish Particle Tracks. Any unsaved data will be lost."
        )
        message_box.setInformativeText("Do you want to save your data?")
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        message_box.setDefaultButton(QMessageBox.Yes)
        reply = message_box.exec()

        if reply == QMessageBox.Yes:
            self._on_click_save()

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
        np = ParticleDecay()
        self.columns = list(np.vars_to_save())
        self.columns += ["magnification"]
        self.columns_show_calibrated = np.vars_to_show(True)
        self.columns_show_uncalibrated = np.vars_to_show(False)
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
        self.set_button_availability()

    def set_button_availability(self) -> None:
        images_imported = False
        for layer in self.viewer.layers:
            if layer.name == "Particle Tracks":
                images_imported = True
                break
        self.set_UI_image_loaded(images_imported, self.bypass_load_screen)
        try:
            selected_row = self._get_selected_row()
            self.save_data_button.setEnabled(True)
            self.delete_particle.setEnabled(True)
            ## think about these two + cal once done.
            self.magnification_button.setEnabled(True)
            self.stereoshift_button.setEnabled(True)
            if self.data[selected_row].index < 4:
                self.radius_button.setEnabled(True)
                self.length_button.setEnabled(True)
                self.decay_angles_button.setEnabled(False)
                return
            elif self.data[selected_row].index == 4:
                self.radius_button.setEnabled(False)
                self.length_button.setEnabled(True)
                self.decay_angles_button.setEnabled(True)
                return
        except IndexError:
            self.delete_particle.setEnabled(False)
            self.radius_button.setEnabled(False)
            self.length_button.setEnabled(False)
            self.decay_angles_button.setEnabled(False)
            # self.apply_magnification_button.setEnabled(False)
            self.stereoshift_button.setEnabled(False)
            # self.magnification_button.setEnabled(False)
            self.save_data_button.setEnabled(False)

    def set_UI_image_loaded(
        self, loaded: bool, bypass_load_screen: bool
    ) -> None:
        if bypass_load_screen:
            self.buttonbox.setContentsMargins(0, 0, 0, 0)
            self.intro_text.hide()
            return
        if loaded:
            # Set margins (left, top, right, bottom)
            self.buttonbox.setContentsMargins(0, 0, 0, 0)
            self.intro_text.hide()
            self.load_button.hide()
            self.particle_decays_menu.show()
            self.delete_particle.show()
            self.radius_button.show()
            self.length_button.show()
            self.decay_angles_button.show()
            self.stereoshift_button.show()
            self.save_data_button.show()
            self.magnification_button.show()
            self.table.show()
            self.apply_magnification_button.show()
        else:
            # Set margins (left, top, right, bottom)
            self.buttonbox.setContentsMargins(200, 0, 200, 0)
            self.intro_text.show()
            self.load_button.show()
            self.particle_decays_menu.hide()
            self.delete_particle.hide()
            self.radius_button.hide()
            self.length_button.hide()
            self.decay_angles_button.hide()
            self.stereoshift_button.hide()
            self.save_data_button.hide()
            self.magnification_button.hide()
            self.table.hide()
            self.apply_magnification_button.hide()

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

    def _on_click_decay_angles(self) -> DecayAnglesDialog:
        """When the 'Calculate decay angles' buttong is clicked, open the decay angles dialog"""
        if (self.decay_angles_dlg is not None) and (
            self.decay_angles_isopen is True
        ):
            self.decay_angles_dlg.raise_()
            return self.decay_angles_dlg
        self.decay_angles_dlg = DecayAnglesDialog(self)
        self.decay_angles_dlg.show()
        point = QPoint(self.pos().x() + self.width(), self.pos().y())
        self.decay_angles_dlg.move(point)
        self.decay_angles_isopen = True
        return self.decay_angles_dlg

    def _on_click_stereoshift(self) -> StereoshiftDialog:
        """When the 'Calculate stereoshift' button is clicked, open stereoshift dialog."""
        # Different behaviour to the Magnification dialog, waiting for the definition of the stereoshift layer structure
        if (self.stereoshift_dlg is not None) and (
            self.stereoshift_isopen is True
        ):
            self.stereoshift_dlg.raise_()
            return self.stereoshift_dlg
        self.stereoshift_dlg = StereoshiftDialog(self)
        self.stereoshift_dlg.show()
        point = QPoint(self.pos().x() + self.width(), self.pos().y())
        self.stereoshift_dlg.move(point)
        self.stereoshift_isopen = True
        return self.stereoshift_dlg

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
        image_count_first = len(glob.glob(folder_subdirs[0] + "/*"))
        more_than_one_image = image_count_first > 1
        same_image_count = all(
            len(glob.glob(subdir + "/*")) == image_count_first
            for subdir in folder_subdirs
        )
        # If all checks are passed, load the images where the event number is a
        # new spatial dimension (stack) and the views are layers.
        if not (
            three_subdirectories
            and subdir_names_contain_views
            and same_image_count
            and more_than_one_image
        ):
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Warning)
            self.msg.setWindowTitle("Data folder structure error")
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.setText(
                "The data folder must contain three subfolders, one for each view, and each subfolder must contain the same number (>1) of images."
            )
            self.msg.show()
            return

        def crop(array):
            # Crops view 1 and 2 to same size as view 3 by removing whitespace
            # on left, as images align on the right.
            # this number is the width of image 3.
            magic_number_smallest_view_pixels = -8377
            return array[:, :, magic_number_smallest_view_pixels:, :]

        # Shuffle the images to avoid bias in the order of the events
        shuffling_indices = np.random.RandomState(
            self.shuffling_seed
        ).permutation(image_count_first)

        stacks = []
        for subdir in folder_subdirs:
            stack: dask.array.Array = imread(subdir + "/*")
            stack = crop(stack)
            # Shuffle each view stack in the same way
            stack = stack[shuffling_indices]
            stacks.append(stack)

        # Concatenate stacks along new spatial dimension such that we have a view, and event slider
        concatenated_stack = dask.array.stack(stacks, axis=0)
        self.viewer.add_image(concatenated_stack, name="Particle Tracks")
        self.viewer.dims.axis_labels = ("View", "Event", "Y", "X")

        # Move to the first event in the series
        self.viewer.dims.set_current_step(1, 0)

        measurement_layer_present = "Radii and Lengths" in self.viewer.layers

        if not measurement_layer_present:
            self.layer_measurements = self.viewer.add_points(
                name="Radii and Lengths",
                size=20,
                border_width=7,
                border_width_is_relative=False,
            )

        # Disable the load button after loading the data (interim solution until we can move to bottom-docked UI)
        self.load_button.setEnabled(False)

    def _on_click_new_particle(self) -> None:
        """When the 'New particle' button is clicked, append a new blank row to
        the table and select the first cell ready to recieve the first point.
        """
        if self.particle_decays_menu.currentIndex() < 1:
            return

        # add a new particle to data
        new_particle = ParticleDecay()
        new_particle.name = self.particle_decays_menu.currentText()
        new_particle.index = self.particle_decays_menu.currentIndex()
        new_particle.magnification_a = self.mag_a
        new_particle.magnification_b = self.mag_b

        # Record the event and view number if the data has been loaded
        # Potentially this could be used to check the measurements are done in the right event
        data_has_been_loaded = "Particle Tracks" in self.viewer.layers
        if data_has_been_loaded:
            new_particle.event_number = self.viewer.dims.current_step[1]
            new_particle.view_number = self.viewer.dims.current_step[0]

        self.data += [new_particle]

        # add particle (== new row) to the table and select it
        self.table.insertRow(self.table.rowCount())
        self.table.selectRow(self.table.rowCount() - 1)
        self.table.setItem(
            self.table.rowCount() - 1,
            self._get_table_column_index("index"),
            QTableWidgetItem(new_particle.index),
        )
        self.table.setItem(
            self.table.rowCount() - 1,
            self._get_table_column_index("name"),
            QTableWidgetItem(new_particle.name),
        )
        self.table.setItem(
            self.table.rowCount() - 1,
            self._get_table_column_index("magnification"),
            QTableWidgetItem(str(new_particle.magnification)),
        )

        print(self.data[-1])
        self.particle_decays_menu.setCurrentIndex(0)

    def _on_click_delete_particle(self) -> None:
        """Delete particle from table and data"""
        try:
            selected_row = self._get_selected_row()
        except IndexError:
            napari.utils.notifications.show_error(
                "There are no particles in the table."
            )
        else:
            confirmation_dialog = QMessageBox()
            confirmation_dialog.setText("Deleting selected particle")
            confirmation_dialog.setInformativeText("Do you want to continue?")
            confirmation_dialog.setStandardButtons(
                QMessageBox.Yes | QMessageBox.Cancel
            )
            confirmation_dialog.setDefaultButton(QMessageBox.Cancel)
            return_code = confirmation_dialog.exec()

            if return_code == QMessageBox.Yes:
                del self.data[selected_row]
                self.table.removeRow(selected_row)

    def _on_click_magnification(self) -> MagnificationDialog:
        """When the 'Calculate magnification' button is clicked, open the magnification dialog"""
        if self.mag_dlg is not None:
            self.mag_dlg.show()
            self.mag_dlg.raise_()
            self.mag_dlg._activate_calibration_layer()
            return self.mag_dlg
        self.mag_dlg = MagnificationDialog(self)
        self.mag_dlg.show()
        point = QPoint(self.pos().x() + self.width(), self.pos().y())
        self.mag_dlg.move(point)
        return self.mag_dlg

    def _propagate_magnification(self, a: float, b: float) -> None:
        """Assigns a and b to the class magnification parameters and to each of the particles in data"""
        self.mag_a = a
        self.mag_b = b
        for particle in self.data:
            particle.magnification_a = a
            particle.magnification_b = b

    def _on_click_apply_magnification(self) -> None:
        """Changes the visualisation of the table to show calibrated values for radius and decay_length"""
        if self.apply_magnification_button.isChecked():
            self._apply_magnification()
        self._set_table_visible_vars(
            self.apply_magnification_button.isChecked()
        )

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
            f.write(",".join(self.data[0].vars_to_save()) + "\n")

            # write the data
            f.writelines([particle.to_csv() for particle in self.data])

        napari.utils.notifications.show_info("Data saved to " + file_name)
