import numpy as np
from napari.layers import Shapes
from napari.utils.events.event import Event
from napari.utils.notifications import show_error
from qtpy.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
)

from ._calculate import angle, track_parameters


class DecayAnglesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # region UI Setup
        self.setWindowTitle("Decay Angles")
        # text boxes for track parameters and results
        self.textboxes_slope = [QLabel(self) for _ in range(3)]
        self.textboxes_intercept = [QLabel(self) for _ in range(3)]
        self.textboxes_phi = [QLabel(self) for _ in range(2)]
        for textbox in (
            self.textboxes_slope
            + self.textboxes_intercept
            + self.textboxes_phi
        ):
            textbox.setMinimumWidth(200)
        # buttons
        btn_calculate = QPushButton("Calculate")
        btn_calculate.clicked.connect(self._on_click_calculate)
        btn_save = QPushButton("Save to table")
        btn_save.clicked.connect(self._on_click_save_to_table)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.buttonBox.clicked.connect(self.reject)

        # layout
        self.setLayout(QGridLayout())
        self.layout().addWidget(
            QLabel("Track parameters (y = a x + b)"), 0, 0, 1, 2
        )
        for i, widget in enumerate(
            [QLabel("Λ"), QLabel("p"), QLabel("π")]
            + self.textboxes_slope
            + self.textboxes_intercept
        ):
            self.layout().addWidget(widget, i % 3 + 1, i // 3)

        self.layout().addWidget(btn_calculate, 4, 0, 1, 3)
        self.layout().addWidget(
            QLabel("Opening angles"),
            5,
            0,
            1,
            3,
        )
        for i, widget in enumerate(
            [QLabel("ϕ_proton [rad]"), QLabel("ϕ_pion [rad]")]
            + self.textboxes_phi
        ):
            self.layout().addWidget(widget, i % 2 + 6, i // 2 + 1)
        self.layout().addWidget(btn_save, 8, 0, 1, 3)
        self.layout().addWidget(self.buttonBox, 10, 0, 1, 3)
        # endregion
        # Setup shapes layer
        self.join_coordinates = [200, 300]
        self.cal_layer: Shapes = self._setup_decayangles_layer()

        # Decay Angles related parameters
        self.phi_proton = 0.0
        self.phi_pion = 0.0
        self.alines = []

        @self.cal_layer.events.data.connect
        def enforce_points_coincident(event: Event) -> None:
            # event.dataindicies says what shape was changed
            # action says what was done to the shape
            # data doesn't get set till user lets go, mouse drag might be better
            match event.index:
                case 0:
                    self.cal_layer.data[1][0] = self.cal_layer.data[0][1]
                    self.cal_layer.data[2][0] = self.cal_layer.data[0][1]
                case 1:
                    self.cal_layer.data[0][1] = self.cal_layer.data[1][0]
                    self.cal_layer.data[2][0] = self.cal_layer.data[1][0]
                case 2:
                    self.cal_layer.data[0][1] = self.cal_layer.data[2][0]
                    self.cal_layer.data[1][0] = self.cal_layer.data[2][0]
            # self.cal_layer.refresh() for some reason calling layer refresh actually stops it refreshing

    def _setup_decayangles_layer(self):
        """Create a shapes layer and add three lines to measure the Lambda, p and pi tracks"""

        # If layer already exists, then assume it was set up previously.
        if "Decay Angles Tool" in self.parent.viewer.layers:
            return self.parent.viewer.layers["Decay Angles Tool"]
        origin_x = self.parent.camera_center[0]
        # note down why this is preferred....
        origin_y = self.parent.camera_center[1]

        zoom_factor = self.parent.viewer.camera.zoom

        # Scale offsets by the inverse of the zoom factor
        lambda_line = np.array(
            [
                [origin_x + -100 / zoom_factor, origin_y + -100 / zoom_factor],
                [origin_x + 100 / zoom_factor, origin_y + 200 / zoom_factor],
            ]
        )
        proton_line = np.array(
            [
                [origin_x + 100 / zoom_factor, origin_y + 200 / zoom_factor],
                [origin_x + 200 / zoom_factor, origin_y + 300 / zoom_factor],
            ]
        )
        pion_line = np.array(
            [
                [origin_x + 100 / zoom_factor, origin_y + 200 / zoom_factor],
                [origin_x + 110 / zoom_factor, origin_y + 300 / zoom_factor],
            ]
        )

        lines = [lambda_line, proton_line, pion_line]
        colors = ["green", "red", "blue"]

        text = {
            "string": ["Λ", "p", "π"],
            "size": 14,
            "color": colors,
            "translation": np.array([-30, 0]),
        }

        shapes_layer = self.parent.viewer.add_shapes(
            lines,
            name="Decay Angles Tool",
            shape_type=["line"] * 3,
            edge_width=5,
            edge_color=colors,
            face_color=colors,
            text=text,
        )
        return shapes_layer

    def _on_click_calculate(self) -> None:
        """When 'Calculate' button is clicked, calculate opening angles and populate table"""

        # Compute tracks and angles
        tracks = [track_parameters(line) for line in self.cal_layer.data]

        self.phi_proton = angle(self.cal_layer.data[0], self.cal_layer.data[1])
        self.phi_pion = angle(self.cal_layer.data[0], self.cal_layer.data[2])

        # # Populate the table
        for slope, intercept, track in zip(
            self.textboxes_slope, self.textboxes_intercept, tracks
        ):
            slope.setText(str(track[0]))
            intercept.setText(str(track[1]))

        self.textboxes_phi[0].setText(str(self.phi_proton))
        self.textboxes_phi[1].setText(str(self.phi_pion))

        # Save points
        self.alines = self.cal_layer.data

    def _on_click_save_to_table(self) -> None:
        """When 'Save to table' button is clicked, propagate stereoshift and depth to main table"""

        # Propagate to particle
        try:
            selected_row = self.parent._get_selected_row()
        except IndexError:
            show_error("There are no particles in the table.")
        else:
            # self.parent.data[selected_row].spoints = self.alines
            self.parent.data[selected_row].phi_proton = self.phi_proton
            self.parent.data[selected_row].phi_pion = self.phi_pion

            # Propagate to parent table
            # for i in range(2):
            #     self.parent.table.setItem(
            #         selected_row,
            #         self.parent._get_table_column_index("sf" + str(i + 1)),
            #         QTableWidgetItem(str(self.spoints[i])),
            #     )
            #     self.parent.table.setItem(
            #         selected_row,
            #         self.parent._get_table_column_index("sp" + str(i + 1)),
            #         QTableWidgetItem(str(self.spoints[i + 2])),
            #     )
            self.parent.table.setItem(
                selected_row,
                self.parent._get_table_column_index("phi_proton"),
                QTableWidgetItem(str(self.phi_proton)),
            )
            self.parent.table.setItem(
                selected_row,
                self.parent._get_table_column_index("phi_pion"),
                QTableWidgetItem(str(self.phi_pion)),
            )

    def reject(self) -> None:
        """On cancel remove the points_Stereoshift layer"""

        # TODO: this is a problem, the layer still exists... not sure how to remove it
        self.parent.viewer.layers.select_previous()
        self.parent.viewer.layers.remove(self.cal_layer)
        self.parent.decay_angles_is_open = False
        return super().reject()
