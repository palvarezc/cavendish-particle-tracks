"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

from datetime import datetime
from typing import List

import napari
import numpy as np
from qtpy.QtCore import QPoint
from qtpy.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ._analysis import (
    EXPECTED_PARTICLES,
    NewParticle,
)
from ._calculate import length, radius
from ._decay_angles_dialog import DecayAnglesDialog
from ._magnification_dialog import MagnificationDialog
from ._set_fiducial_dialog import Set_Fiducial_Dialog
from ._stereoshift_dialog import StereoshiftDialog


class ParticleTracksWidget(QWidget):
    """Widget containing a simple table of points and track radii per image."""

    def __init__(self, napari_viewer: napari.Viewer):
        super().__init__()
        self.viewer = napari_viewer

        def setup_ui(self):
            # define QtWidgets
            # why is this self. and the others added after?
            self.btn_load = QPushButton("Load data")
            self.cb = QComboBox()
            self.cb.addItems(EXPECTED_PARTICLES)
            self.cb.setCurrentIndex(0)
            self.cb.currentIndexChanged.connect(self._on_click_new_particle)
            btn_delete_particle = QPushButton("Delete particle")
            btn_radius = QPushButton("Calculate radius")
            btn_length = QPushButton("Calculate length")
            btn_decayangle = QPushButton("Calculate decay angles")
            btn_stereoshift = QPushButton("Stereoshift")
            btn_testnew = QPushButton("test new reference")
            btn_save = QPushButton("Save")
            self.mag = QPushButton("Magnification")

            # setup particle table
            self.table = self._set_up_table()
            self._set_table_visible_vars(False)

            # Apply magnification disabled until the magnification parameters are computed
            self.cal = QRadioButton("Apply magnification")
            self.cal.setEnabled(False)

            # connect callbacks
            # NOTE: This isn't consistent in the code structure. Connects for the combobox etc have been done above.
            self.btn_load.clicked.connect(self._on_click_load)
            btn_delete_particle.clicked.connect(self._on_click_delete_particle)
            btn_radius.clicked.connect(self._on_click_radius)
            btn_length.clicked.connect(self._on_click_length)
            btn_decayangle.clicked.connect(self._on_click_decay_angles)
            btn_stereoshift.clicked.connect(self._on_click_stereoshift)
            self.cal.toggled.connect(self._on_click_apply_magnification)
            btn_save.clicked.connect(self._on_click_save)
            btn_testnew.clicked.connect(self._on_click_newref)

            self.mag.clicked.connect(self._on_click_magnification)
            # TODO: find which of thsese works
            # https://napari.org/stable/gallery/custom_mouse_functions.html
            # self.viewer.mouse_press.callbacks.connect(self._on_mouse_press)
            # self.viewer.events.mouse_press(self._on_mouse_click)

            # layout
            self.setLayout(QVBoxLayout())
            self.layout().addWidget(self.load)
            self.layout().addWidget(self.cb)
            self.layout().addWidget(btn_delete_particle)
            self.layout().addWidget(btn_radius)
            self.layout().addWidget(btn_length)
            self.layout().addWidget(btn_decayangle)
            self.layout().addWidget(self.table)
            self.layout().addWidget(self.cal)
            self.layout().addWidget(btn_stereoshift)
            self.layout().addWidget(self.mag)
            self.layout().addWidget(btn_save)
            self.layout().addWidget(btn_testnew)

        setup_ui(self)
        # Data analysis
        self.data: List[NewParticle] = []
        # might not need this eventually
        self.mag_a = -1.0
        self.mag_b = 0.0

        @self.viewer.mouse_drag_callbacks.append
        def _on_mouse_click(viewer, event):
            print("Mouse click")

    def _get_selected_points(self, layer_name="Points") -> np.array:
        """Returns array of selected points in the viewer"""

        # Filtering selected points
        points_layers = [
            layer for layer in self.viewer.layers if layer.name == layer_name
        ]
        try:
            selected_points = np.array(
                [
                    points_layers[0].data[i]
                    for i in points_layers[0].selected_data
                ]
            )
        except IndexError:
            selected_points = []
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

        # Assigns the points and radius to the selected row
        selected_row = self._get_selected_row()
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
        selected_row = self._get_selected_row()
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

        test_file_dialog = QFileDialog(self)
        test_file_dialog.setFileMode(QFileDialog.Directory)
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
        three_subdirectories = len(folder_subdirs) == 3
        subdir_names_contain_views = all(
            any(view in name.lower() for name in folder_subdirs)
            for view in VIEW_NAMES
        )
        same_image_count = all(
            len(glob.glob(subdir + "/*"))
            == len(glob.glob(folder_subdirs[0] + "/*"))
            for subdir in folder_subdirs
        )
        if not (
            three_subdirectories
            and subdir_names_contain_views
            and same_image_count
        ):
            print(
                "WARNING: The data folder must contain three subfolders, one for each view, and each subfolder must contain the same number of images."
            )
            # TODO: make this a QWarningBox?
            return

        for subdir, stack_name in zip(
            folder_subdirs, ["stack1", "stack2", "stack3"]
        ):
            stack = imread(subdir + "/*")
            self.viewer.add_image(stack, name=stack_name)
            # TODO: investigate the multiscale otption.

    def _on_click_newref(self) -> Set_Fiducial_Dialog:
        """When the 'test new reference' button is clicked, open the set fiducial dialog."""
        dlg = Set_Fiducial_Dialog(self)
        dlg.show()
        point = QPoint(self.pos().x() + self.width(), self.pos().y())
        dlg.move(point)
        return

    def _on_click_new_particle(self) -> None:
        """When the 'New particle' button is clicked, append a new blank row to
        the table and select the first cell ready to recieve the first point.
        """
        if self.cb.currentIndex() < 1:
            return

        # add new particle to data
        np = NewParticle()
        np.Name = self.cb.currentText()
        np.magnification_a = self.mag_a
        np.magnification_b = self.mag_b
        self.data += [np]

        # add particle (== new row) to the table and select it
        self.table.insertRow(self.table.rowCount())
        self.table.selectRow(self.table.rowCount() - 1)
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

    def _on_click_magnification(self) -> None:
        """When the 'Calculate magnification' button is clicked, open the magnification dialog"""

        dlg = MagnificationDialog(self)
        dlg.show()
        point = QPoint(self.pos().x() + self.width(), self.pos().y())
        dlg.move(point)

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
        """Save list of particles to csv file"""

        if not len(self.data):
            print("No data to be saved")
            return

        filename = str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S")) + ".csv"

        with open(filename, "w", encoding="UTF8", newline="") as f:
            # write the header
            f.write(",".join(self.data[0]._vars_to_save()) + "\n")

            # write the data
            f.writelines([particle.to_csv() for particle in self.data])

        print("Saved data to ", filename)
