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
    FIDUCIALS,
    NewParticle,
)
from ._calculate import length, radius
from ._decay_angles_dialog import DecayAnglesDialog
from ._magnification_dialog import MagnificationDialog
from ._stereoshift_dialog import StereoshiftDialog


class ParticleTracksWidget(QWidget):
    """Widget containing a simple table of points and track radii per image."""

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__()
        self.viewer = napari_viewer

        # define QtWidgets
        # why is this self. and the others added after?
        self.cb = QComboBox()
        self.cb.addItems(EXPECTED_PARTICLES)
        self.cb.setCurrentIndex(0)
        self.cb.currentIndexChanged.connect(self._on_click_new_particle)
        btn_radius = QPushButton("Calculate radius")
        btn_length = QPushButton("Calculate length")
        btn_decayangle = QPushButton("Calculate decay angles")
        cmb_fiducial = QComboBox()
        cmb_fiducial.addItems(FIDUCIALS)
        cmb_fiducial.currentIndexChanged.connect(self._on_click_add_fiducial)
        btn_stereoshift = QPushButton("Stereoshift")
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
        btn_radius.clicked.connect(self._on_click_radius)
        btn_length.clicked.connect(self._on_click_length)
        btn_decayangle.clicked.connect(self._on_click_decay_angles)
        btn_stereoshift.clicked.connect(self._on_click_stereoshift)
        self.cal.toggled.connect(self._on_click_apply_magnification)
        btn_save.clicked.connect(self._on_click_save)

        self.mag.clicked.connect(self._on_click_magnification)
        # TODO: find which of thsese works
        # https://napari.org/stable/gallery/custom_mouse_functions.html
        # self.viewer.mouse_press.callbacks.connect(self._on_mouse_press)
        # self.viewer.events.mouse_press(self._on_mouse_click)

        # layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.cb)
        self.layout().addWidget(btn_radius)
        self.layout().addWidget(btn_length)
        self.layout().addWidget(btn_decayangle)
        self.layout().addWidget(self.table)
        self.layout().addWidget(self.cal)
        self.layout().addWidget(btn_stereoshift)
        self.layout().addWidget(self.mag)
        self.layout().addWidget(cmb_fiducial)
        self.layout().addWidget(btn_save)

        # Data analysis
        self.data: List[NewParticle] = []
        # might not need this eventually
        self.mag_a = -1.0
        self.mag_b = 0.0

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

    def _on_click_add_fiducial(self) -> None:
        """Adds a fiducial marker to the layer."""
        # currently, this is implemented by adding the layer, then a point.
        # ideally this should resemble the inbuilt tools, but let's get it working first.

        point = [100, 100]
        # this should be done properly later, currently copying the old approach
        # get below to reference the currently selected fiducial in the combobox
        name = "Example C'"
        point_label = {
            "string": name,
            "size": 20,
            "color": "green",
            "translation": np.array([-30, 0]),
        }
        # see stereoshift_dialog
        # create a points layer here if one doesn't exist.
        # reuse code from other sections here to achieve that.
        points_layer = self.parent.viewer.add_point(
            point,
            name="Fiducials",
            # text=...
            # size=20,
            border_width=5,
            # border_width_is_relative=True,
            # border_color=colors,
            # face_color=colors,
        )
        print("This is a placeholder function.")
