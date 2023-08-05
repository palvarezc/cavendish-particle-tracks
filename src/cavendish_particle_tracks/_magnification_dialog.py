from typing import List

from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from cavendish_particle_tracks._analysis import (
    FIDUCIAL_BACK,
    FIDUCIAL_FRONT,
    Fiducial,
)
from cavendish_particle_tracks._calculate import magnification


class MagnificationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent

        self.setWindowTitle("Magnification")

        self.f1 = Fiducial()
        self.f2 = Fiducial()
        self.b1 = Fiducial()
        self.b2 = Fiducial()

        # drop-down lists of fiducials
        self.cbf1 = self._setup_dropdown_fiducials_combobox()
        self.cbf2 = self._setup_dropdown_fiducials_combobox()
        self.cbb1 = self._setup_dropdown_fiducials_combobox(back=True)
        self.cbb2 = self._setup_dropdown_fiducials_combobox(back=True)

        # text boxes
        self.txf1 = QLabel(self)
        self.txf2 = QLabel(self)
        self.txb1 = QLabel(self)
        self.txb2 = QLabel(self)

        self.txboxes = [self.txf1, self.txf2, self.txb1, self.txb2]
        for txt in self.txboxes:
            txt.setMinimumWidth(200)

        # add coords buttons
        self.cof1 = QPushButton("Add")
        self.cof2 = QPushButton("Add")
        self.cob1 = QPushButton("Add")
        self.cob2 = QPushButton("Add")
        self.cof1.clicked.connect(self._on_click_add_coords_f1)
        self.cof2.clicked.connect(self._on_click_add_coords_f2)
        self.cob1.clicked.connect(self._on_click_add_coords_b1)
        self.cob2.clicked.connect(self._on_click_add_coords_b2)

        self.bmag = QPushButton("Calculate magnification")
        self.bmag.clicked.connect(self._on_click_magnification)

        self.table = QTableWidget(1, 2)
        self.table.setHorizontalHeaderLabels(["a", "b"])

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # layout
        self.setLayout(QGridLayout())
        self.layout().addWidget(
            QLabel("Select front fiducial marks"), 0, 0, 1, 3
        )
        for i, widget in enumerate(
            [self.cbf1, self.txf1, self.cof1, self.cbf2, self.txf2, self.cof2]
        ):
            self.layout().addWidget(widget, i // 3 + 1, i % 3)
        self.layout().addWidget(
            QLabel("Select back fiducial marks"), 3, 0, 1, 3
        )
        for i, widget in enumerate(
            [self.cbb1, self.txb1, self.cob1, self.cbb2, self.txb2, self.cob2]
        ):
            self.layout().addWidget(widget, i // 3 + 4, i % 3)

        self.layout().addWidget(self.bmag, 6, 0, 1, 3)

        self.layout().addWidget(
            QLabel("Magnification parameters (M = a + b z)"), 7, 0, 1, 3
        )
        self.layout().addWidget(self.table, 8, 0, 1, 3)

        self.layout().addWidget(self.buttonBox, 9, 0, 1, 3)

        self.cal_layer = self.parent.viewer.add_points(
            name="Points_Calibration"
        )

    def _setup_dropdown_fiducials_combobox(self, back=False):
        """Sets up a drop-down list of fiducials for the `back` or front (`back=False`)."""
        combobox = QComboBox()
        if back:
            combobox.addItems(FIDUCIAL_BACK.keys())
        else:
            combobox.addItems(FIDUCIAL_FRONT.keys())
        combobox.currentIndexChanged.connect(self._on_click_fiducial)
        return combobox

    def _on_click_fiducial(self) -> None:
        """When fiducial is selected, we locate ourselves in the Points_calibration layer and select option 'Add point'"""

        # Would be cool if we could wait for a click here and add that as the selected fiducial, but no clue how to do that yet
        # layers  = [
        #     layer for layer in self.parent.viewer.layers if layer.name == "Points_Calibration"
        # ]
        # layer = layers[0]
        # @layer.mouse_drag_callbacks.append
        # def callback(layer, event):  # (0,0) is the center of the upper left pixel
        #     print(self.parent.viewer.cursor.position)

        print("Add fiducial point")

    def _on_click_add_coords_f1(self) -> None:
        """Add first front fiducial"""
        self.f1.name = self.cbf1.currentText()
        self.f1.x, self.f2.y = self._add_coords(0)

    def _on_click_add_coords_f2(self) -> None:
        """Add first front fiducial"""
        self.f2.name = self.cbf2.currentText()
        self.f2.x, self.f2.y = self._add_coords(1)

    def _on_click_add_coords_b1(self) -> None:
        """Add first front fiducial"""
        self.b1.name = self.cbb1.currentText()
        self.b1.x, self.b1.y = self._add_coords(2)

    def _on_click_add_coords_b2(self) -> None:
        """Add first front fiducial"""
        self.b2.name = self.cbb2.currentText()
        self.b2.x, self.b2.y = self._add_coords(3)

    def _add_coords(self, fiducial: int) -> List[float]:
        """When 'Add' is selected, the selected point is added to the corresponding fiducial text box"""

        selected_points = self.parent._get_selected_points(
            "Points_Calibration"
        )

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

    def accept(self) -> None:
        """On accept propagate the calibration information to the main window and remove the points_Calibration layer"""

        print("Propagating magnification to table.")
        self.parent._propagate_magnification(self.a, self.b)
        # TODO: this is a problem, the layer still exists... not sure how to remove it
        self.parent.viewer.layers.select_previous()
        self.parent.viewer.layers.remove(self.cal_layer)
        self.parent.cal.setEnabled(True)
        # self.parent.mag.setEnabled(False)
        self.parent.mag.setText("Update magnification")
        return super().accept()

    def reject(self) -> None:
        """On reject remove the points_Calibration layer"""

        # This is a problem, the layer still exists... not sure how to remove it
        self.parent.viewer.layers.select_previous()
        self.parent.viewer.layers.remove(self.cal_layer)
        return super().reject()
