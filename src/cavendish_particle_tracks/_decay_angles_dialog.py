import napari
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

ANGLES_LAYER_NAME = "Decay Angles Tool"


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
            self.textboxes_slope + self.textboxes_intercept + self.textboxes_phi
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
        self.layout().addWidget(QLabel("Track parameters (y = a x + b)"), 0, 0, 1, 2)

        for i, column_title in enumerate([QLabel("Gradient, a"), QLabel("Intercept, b")]):
            self.layout().addWidget(column_title, 1, i + 1)

        for i, table_datum in enumerate(
            [QLabel("Λ"), QLabel("p"), QLabel("π")]
            + self.textboxes_slope
            + self.textboxes_intercept
        ):
            self.layout().addWidget(table_datum, i % 3 + 2, i // 3)

        self.layout().addWidget(btn_calculate, 5, 0, 1, 3)
        self.layout().addWidget(
            QLabel("Opening angles"),
            6,
            0,
            1,
            3,
        )
        for i, widget in enumerate(
            [QLabel("ϕ_proton [rad]"), QLabel("ϕ_pion [rad]")] + self.textboxes_phi
        ):
            self.layout().addWidget(widget, i % 2 + 7, i // 2 + 1)
        self.layout().addWidget(btn_save, 9, 0, 1, 3)
        self.layout().addWidget(self.buttonBox, 11, 0, 1, 3)
        # endregion
        # Setup shapes layer
        self.join_coordinates = [200, 300]
        self.cal_layer: Shapes = self._setup_decayangles_layer()
        self.cal_layer.events.data.connect(self._enforce_points_coincident)

        # # This almost gets the behavior we want, but only for the line labels
        # def enforce_points_coincident_v2(event: Event) -> None:
        #     (selected_shape,) = self.cal_layer.selected_data
        #     data = self.cal_layer.data
        #     if len(data) != 3:
        #         return
        #     if selected_shape==0 and (data[0][0] != data[1][0]).all():
        #         # # This is what we want but needs private methods
        #         # vertices = self.cal_layer._data_view.shapes[1].data
        #         # vertices[0] = data[0][0]
        #         # self.cal_layer._data_view.edit(1, vertices, new_type=None)
        #         # self.cal_layer.refresh()
        #         data[1][0][0] = data[0][0][0]
        #         data[1][0][1] = data[0][0][1]
        #         self.cal_layer.refresh()
        # self.cal_layer.events.set_data.connect(enforce_points_coincident_v2)

        # Decay Angles related parameters
        self.phi_proton = 0.0
        self.phi_pion = 0.0
        self.alines = []

    def _enforce_points_coincident(self, event: Event) -> None:
        # event.data_indices says what shape was changed
        # action says what was done to the shape
        # data doesn't get set till user lets go, mouse drag might be better, but not sure how to implement it
        # Maybe the long term solution is to have a custom shape?
        if event.action == "changed":
            shapes_modified = event.data_indices
            data = self.cal_layer.data
            if len(shapes_modified) == 3:
                # if all shapes were modified, this must be a translation of the three shapes
                # do nothing.
                return
            elif len(shapes_modified) == 2:
                # if two of them have been moved, move the third one (if it has not been moved already)
                for i in range(3):
                    if (i not in shapes_modified) and (
                        self.cal_layer.data[i][0]
                        != self.cal_layer.data[shapes_modified[0]][0]
                    ).any():
                        data[i][0] = self.cal_layer.data[shapes_modified[0]][0]
                        self.cal_layer.data = data
            elif len(shapes_modified) == 1:
                # if only one has been moved, move the other two (if they have not been moved already)
                for i in range(3):
                    if (i not in shapes_modified) and (
                        self.cal_layer.data[i][0]
                        != self.cal_layer.data[shapes_modified[0]][0]
                    ).any():
                        data[i][0] = self.cal_layer.data[shapes_modified[0]][0]
                        self.cal_layer.data = data
            else:
                # nothing moved, or more shapes have been added
                # do nothing
                return

    def _setup_decayangles_layer(self):
        """Create a shapes layer and add three lines to measure the Lambda, p and pi tracks"""

        # If layer already exists, then assume it was set up previously.
        if ANGLES_LAYER_NAME in self.parent.viewer.layers:
            return self.parent.viewer.layers[ANGLES_LAYER_NAME]
        origin_x = self.parent.camera_center[0]
        # note down why this is preferred....
        origin_y = self.parent.camera_center[1]

        zoom_factor = self.parent.viewer.camera.zoom

        # The first point for all tracks is the decay vertex
        # Scale offsets by the inverse of the zoom factor
        lambda_line = np.array(
            [
                [origin_x + 100 / zoom_factor, origin_y + 200 / zoom_factor],
                [origin_x + -100 / zoom_factor, origin_y + -100 / zoom_factor],
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
            "size": 20,
            "color": colors,
            "translation": np.array([-30, 0]),
        }

        shapes_layer = self.parent.viewer.add_shapes(
            lines,
            name=ANGLES_LAYER_NAME,
            shape_type=["line"] * 3,
            edge_width=5,
            edge_color=colors,
            face_color=colors,
            text=text,
        )
        return shapes_layer

    def _on_click_calculate(self) -> None:
        """When 'Calculate' button is clicked, calculate opening angles and populate table"""

        # The Lambda travels towards the decay vertex, line needs to be reversed
        lambda_line = self.cal_layer.data[0][::-1]
        proton_line = self.cal_layer.data[1]
        pion_line = self.cal_layer.data[2]

        # Save the lines
        self.alines = [lambda_line, proton_line, pion_line]

        # Compute tracks and angles
        tracks = [track_parameters(line) for line in self.alines]

        self.phi_proton = angle(lambda_line, proton_line)
        self.phi_pion = angle(lambda_line, pion_line)

        # # Populate the table
        for slope, intercept, track in zip(
            self.textboxes_slope, self.textboxes_intercept, tracks
        ):
            slope.setText(str(track[0]))
            intercept.setText(str(track[1]))

        self.textboxes_phi[0].setText(str(self.phi_proton))
        self.textboxes_phi[1].setText(str(self.phi_pion))

    def _on_click_save_to_table(self) -> None:
        """When 'Save to table' button is clicked, propagate stereoshift and depth to main table"""

        # Propagate to particle
        try:
            selected_row = self.parent._get_selected_row()
        except IndexError:
            show_error("There are no particles in the table.")
        else:
            # self.parent.data[selected_row].alines = self.alines
            self.parent.data[selected_row].phi_proton = self.phi_proton
            self.parent.data[selected_row].phi_pion = self.phi_pion

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
        napari.utils.notifications.show_info(
            "Decay angles saved to particle " + str(selected_row)
        )

    def reject(self) -> None:
        """On cancel remove the points_Stereoshift layer"""
        self.parent._deactivate_calibration_layer(self.cal_layer)
        return super().reject()
