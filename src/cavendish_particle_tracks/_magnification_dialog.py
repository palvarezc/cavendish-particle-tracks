from typing import TYPE_CHECKING

from napari.layers import Points
from qtpy.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from ._analysis import (
    FIDUCIAL_BACK,
    FIDUCIAL_FRONT,
    Fiducial,
)
from ._calculate import magnification

if TYPE_CHECKING:
    from ._main_widget import ParticleTracksWidget


class MagnificationDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)  # Call QDialog constructor
        self.parent: ParticleTracksWidget = parent
        self.setWindowTitle("Magnification")

        self.f1 = Fiducial()
        self.f2 = Fiducial()
        self.b1 = Fiducial()
        self.b2 = Fiducial()

        # region UI Setup
        self.ui_setup()
        self.magnification_layer = (
            self.create_or_retrieve_magnification_layer()
        )

    def create_or_retrieve_magnification_layer(self) -> Points:
        if "Magnification" in self.parent.viewer.layers:
            return self.parent.viewer.layers["Magnification"]
        return self.parent.viewer.add_points(name="Magnification")

    def ui_setup(self):
        self.setWindowTitle("Magnification")
        # Drop-down selection of Fiducials
        self.cmb_front1 = self._setup_dropdown_fiducials_combobox()
        self.cmb_front2 = self._setup_dropdown_fiducials_combobox()
        self.cmb_back1 = self._setup_dropdown_fiducials_combobox(back=True)
        self.cmb_back2 = self._setup_dropdown_fiducials_combobox(back=True)
        # text boxes indicating the coordinates of the fiducials
        self.txt_f1coord = QLabel(self)  # front fiducial 1
        self.txt_f2coord = QLabel(self)  # front fiducial 2
        self.txt_b1coord = QLabel(self)  # back fiducial 1
        self.txt_b2coord = QLabel(self)  # back fiducial 2
        self.txboxes = [
            self.txt_f1coord,
            self.txt_f2coord,
            self.txt_b1coord,
            self.txt_b2coord,
        ]
        for txt in self.txboxes:
            txt.setMinimumWidth(200)
        # Add selected fiducial buttons
        self.add_f1_button = QPushButton("Add")
        self.add_f2_button = QPushButton("Add")
        self.add_b1_button = QPushButton("Add")
        self.add_b2_button = QPushButton("Add")
        self.add_f1_button.clicked.connect(self._on_click_add_coords_f1)
        self.add_f2_button.clicked.connect(self._on_click_add_coords_f2)
        self.add_b1_button.clicked.connect(self._on_click_add_coords_b1)
        self.add_b2_button.clicked.connect(self._on_click_add_coords_b2)
        self.calculate_magnification_button = QPushButton(
            "Calculate magnification"
        )
        self.calculate_magnification_button.clicked.connect(
            self._on_click_magnification
        )
        # Add table to show the resultant magnification parameter
        self.table = QTableWidget(1, 2)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(["a", "b"])
        # Add Ok/Cancel button box
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Set GUI Layout
        self.setLayout(QGridLayout())
        self.layout().addWidget(
            QLabel("Select front fiducial marks"), 0, 0, 1, 3
        )
        for i, widget in enumerate(
            [
                self.cmb_front1,
                self.txt_f1coord,
                self.add_f1_button,
                self.cmb_front2,
                self.txt_f2coord,
                self.add_f2_button,
            ]
        ):
            self.layout().addWidget(widget, i // 3 + 1, i % 3)
        self.layout().addWidget(
            QLabel("Select back fiducial marks"), 3, 0, 1, 3
        )
        for i, widget in enumerate(
            [
                self.cmb_back1,
                self.txt_b1coord,
                self.add_b1_button,
                self.cmb_back2,
                self.txt_b2coord,
                self.add_b2_button,
            ]
        ):
            self.layout().addWidget(widget, i // 3 + 4, i % 3)

        self.layout().addWidget(
            self.calculate_magnification_button, 6, 0, 1, 3
        )
        self.layout().addWidget(
            QLabel("Magnification parameters (M = a + b z)"), 7, 0, 1, 3
        )
        self.layout().addWidget(self.table, 8, 0, 1, 3)

        self.layout().addWidget(self.buttonBox, 9, 0, 1, 3)

        self.a = self.parent.mag_a
        self.b = self.parent.mag_b

    def _setup_dropdown_fiducials_combobox(self, back=False):
        """Sets up a drop-down list of fiducials for the `back` or front (`back=False`)."""
        combobox = QComboBox()
        if back:
            combobox.addItems(FIDUCIAL_BACK.keys())
        else:
            combobox.addItems(FIDUCIAL_FRONT.keys())
        return combobox

    def _on_click_add_coords_f1(self) -> None:
        """Add first front fiducial"""
        self.f1.name = self.cmb_front1.currentText()
        self.f1.x, self.f1.y = self._add_coords(0)

    def _on_click_add_coords_f2(self) -> None:
        """Add second front fiducial"""
        self.f2.name = self.cmb_front2.currentText()
        self.f2.x, self.f2.y = self._add_coords(1)

    def _on_click_add_coords_b1(self) -> None:
        """Add first back fiducial"""
        self.b1.name = self.cmb_back1.currentText()
        self.b1.x, self.b1.y = self._add_coords(2)

    def _on_click_add_coords_b2(self) -> None:
        """Add second back fiducial"""
        self.b2.name = self.cmb_back2.currentText()
        self.b2.x, self.b2.y = self._add_coords(3)

    def _add_coords(self, fiducial: int) -> list[float]:
        """When 'Add' is selected, the selected point is added to the corresponding fiducial text box"""

        selected_points = self.parent._get_selected_points("Magnification")

        # Forcing only 1 points
        if len(selected_points) != 1:
            print("Select (only) one point to add fiducial.")
            return [-1.0e6, -1.0e6]

        textbox = self.txboxes[fiducial]
        textbox.setText(str(selected_points[0]))

        return selected_points[0]

    def _on_click_magnification(self) -> None:
        """When 'Calculate magnification' button is clicked, calculate magnification and populate table"""

        # Need something like this but a bit better
        if not (
            self.f1.name and self.f2.name and self.b1.name and self.b2.name
        ):
            print("Select fiducials to calcuate the magnification")
            return

        self.a, self.b = magnification(self.f1, self.f2, self.b1, self.b2)

        self.table.setItem(0, 0, QTableWidgetItem(str(self.a)))
        self.table.setItem(0, 1, QTableWidgetItem(str(self.b)))

    def _activate_calibration_layer(self):
        """Show the calibration layer and move it to the top"""
        self.magnification_layer.visible = True
        # Move the calibration layer to the top
        self.parent.viewer.layers.move(
            self.parent.viewer.layers.index(self.magnification_layer),
            len(self.parent.viewer.layers),
        )
        self.parent.viewer.layers.selection.active = self.magnification_layer

    def _deactivate_calibration_layer(self):
        """Hide the calibration layer and move it to the bottom"""
        # self.parent.viewer.layers.select_previous()
        self.magnification_layer.visible = False
        # Move the calibration layer to the bottom
        self.parent.viewer.layers.move(
            self.parent.viewer.layers.index(self.magnification_layer), 0
        )

    def accept(self) -> None:
        """On accept propagate the calibration information to the main window and remove the Magnification layer"""

        print("Propagating magnification to table.")
        self.parent._propagate_magnification(self.a, self.b)
        self._deactivate_calibration_layer()
        self.parent.apply_magnification_button.setEnabled(True)
        # self.parent.mag.setEnabled(False)
        self.parent.magnification_button.setText("Update magnification")
        return super().accept()

    def reject(self) -> None:
        """On reject remove the magnification layer"""

        self._deactivate_calibration_layer()
        return super().reject()
