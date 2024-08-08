import numpy as np
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
)

from ._analysis import FIDUCIAL_BACK, FIDUCIAL_FRONT, Fiducial
from ._calculate import depth, length, magnification, stereoshift


class StereoshiftDialog(QDialog):
    def __init__(self, parent=None):
        # Call parent constructor
        super().__init__(parent)

        # Declare instance variables + constants
        self.parent = parent
        FIDUCIAL_VIEWS = [
            "Back fiducial view1",
            "Back fiducial view2",
            "Point view1",
            "Point view2",
        ]
        # Stereoshift related parameters
        # TODO figure out what these are
        self.shift_fiducial = 0.0
        self.shift_point = 0.0
        self.point_stereoshift = 0.0
        self.point_depth = -1.0
        self.spoints = []
        self._fiducial_views = [
            Fiducial(view_name) for view_name in FIDUCIAL_VIEWS
        ]
        # Setup points layer with stereoshift markers
        self.cal_layer = self._setup_stereoshift_layer()
        # region UI Setup
        self.setWindowTitle("Stereoshift")
        # drop-down lists of fiducials
        # TODO write what this combobox is for
        self.cmb_ref_fiducial = QComboBox()
        self.cmb_ref_fiducial.addItem("Front / Back")
        self.cmb_ref_fiducial.addItem("Back / Front")
        self.cmb_ref_fiducial.currentIndexChanged.connect(
            self._on_click_cmb_ref_fiducial
        )
        # Labels for the points' coordinates
        lviewf1 = QLabel("View 1")
        lviewf2 = QLabel("View 2")
        lviewb1 = QLabel("View 1")
        lviewb2 = QLabel("View 2")
        # Textboxes for the output of point coordinates
        self.textboxes = [QLabel(self) for _ in range(4)]
        # Texbox with calculation formula
        self.label_stereoshift = QLabel(
            "Stereo shift (shift_p/shift_f = depth_p/depth_f)"
        )
        # Textboxes for calculation results
        self.tshift_fiducial = QLabel(self)
        self.tshift_point = QLabel(self)
        self.tstereoshift = QLabel(self)
        self.tdepth = QLabel(self)
        self.results = [
            self.tshift_fiducial,
            self.tshift_point,
            self.tstereoshift,
            self.tdepth,
        ]
        # Set minimum width for textboxes
        for textbox in self.textboxes + self.results:
            textbox.setMinimumWidth(200)
        # Control Buttons
        btn_calculate = QPushButton("Calculate")
        btn_calculate.clicked.connect(self._on_click_calculate)
        btn_save = QPushButton("Save to table")
        btn_save.clicked.connect(self._on_click_save_to_table)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.buttonBox.clicked.connect(self.cancel)
        # layout
        """
        For legibility of code, perhaps the declarations of all GUI
        objects should go together, rather than some being here
        and the rest being placed above.
        Otherwise, it can become difficult to imagine what the GUI looks like
        without having seen an image of it.
        """
        self.setLayout(QGridLayout())
        self.layout().addWidget(
            QLabel("Select Reference / Fiducial"), 0, 0, 1, 2
        )
        self.layout().addWidget(QLabel("Fiducial coordinates"), 1, 0, 1, 2)
        self.layout().addWidget(self.cmb_ref_fiducial, 0, 2)
        for i, widget in enumerate(
            [lviewf1, self.textboxes[0], lviewf2, self.textboxes[1]]
        ):
            self.layout().addWidget(widget, i // 2 + 2, i % 2 + 1)
        self.layout().addWidget(QLabel("Point coordinates"), 4, 0, 1, 2)
        for i, widget in enumerate(
            [lviewb1, self.textboxes[2], lviewb2, self.textboxes[3]]
        ):
            self.layout().addWidget(widget, i // 2 + 5, i % 2 + 1)

        self.layout().addWidget(btn_calculate, 7, 0, 1, 3)

        self.layout().addWidget(
            self.label_stereoshift,
            8,
            0,
            1,
            3,
        )
        # self.layout().addWidget(self.table, 9, 0, 1, 3)
        self.layout().addWidget(QLabel("Fiducial shift"), 9, 1)
        self.layout().addWidget(self.tshift_fiducial, 9, 2)
        self.layout().addWidget(QLabel("Point shift"), 10, 1)
        self.layout().addWidget(self.tshift_point, 10, 2)
        self.layout().addWidget(QLabel("Ratio"), 11, 1)
        self.layout().addWidget(self.tstereoshift, 11, 2)
        self.layout().addWidget(QLabel("Point depth (cm)"), 12, 1)
        self.layout().addWidget(self.tdepth, 12, 2)
        self.layout().addWidget(btn_save, 13, 0, 1, 3)
        self.layout().addWidget(self.buttonBox, 14, 0, 1, 3)
        # endregion

    def _setup_stereoshift_layer(self):
        # add the points
        points = np.array(
            [
                [100, 100],
                [100, 150],
                [200, 300],
                [333, 111],
                [400, 350],
                [500, 150],
            ]
        )

        labels = ["Reference (Front) view1", "Reference (Front) view2"]
        for item in self._fiducial_views:
            labels += [item.name]

        colors = ["green", "green", "blue", "blue", "red", "red"]

        text = {
            "string": labels,
            "size": 20,
            "color": colors,
            "translation": np.array([-30, 0]),
        }

        points_layer = self.parent.viewer.add_points(
            points,
            name="Points_Stereoshift",
            text=text,
            size=20,
            edge_width=7,
            edge_width_is_relative=False,
            edge_color=colors,
            face_color=colors,
        )

        return points_layer

    def f(self, i) -> Fiducial:
        """Returns the front fiducial item, except when it selects the back"""
        if i not in [1, 2]:
            raise IndexError()
        return self._fiducial_views[i - 1]

    def b(self, i) -> Fiducial:
        """Returns the back fiducial item"""
        if i not in [1, 2]:
            raise IndexError()
        return self._fiducial_views[i + 1]

    def _on_click_cmb_ref_fiducial(self) -> None:
        """When the user selects which set of fiducials is used as the reference, update the name of the fiducial"""

        if self.cmb_ref_fiducial.currentIndex() == 0:
            self.f(1).name = "Back fiducial view1"
            self.f(2).name = "Back fiducial view2"
            self.cal_layer.text.string.array[0] = "Reference (Front) view1"
            self.cal_layer.text.string.array[1] = "Reference (Front) view2"
            self.cal_layer.text.string.array[2] = self.f(1).name
            self.cal_layer.text.string.array[3] = self.f(2).name
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = depth_p/depth_f)"
            )

        if self.cmb_ref_fiducial.currentIndex() == 1:
            self.f(1).name = "Front fiducial view1"
            self.f(2).name = "Front fiducial view2"
            self.cal_layer.text.string.array[0] = "Reference (Back) view1"
            self.cal_layer.text.string.array[1] = "Reference (Back) view2"
            self.cal_layer.text.string.array[2] = self.f(1).name
            self.cal_layer.text.string.array[3] = self.f(2).name
            self.label_stereoshift.setText(
                "Stereo shift (shift_p/shift_f = 1 - depth_p/depth_f)"
            )

        self.cal_layer.refresh()

    def _on_click_calculate(self) -> None:
        """When 'Calculate' button is clicked, calculate stereoshift and populate table"""

        # Add points coords to corresponding text box
        for i in range(len(self._fiducial_views)):
            (
                self._fiducial_views[i].x,
                self._fiducial_views[i].y,
            ) = (
                self.cal_layer.data[i + 2] - self.cal_layer.data[i % 2]
            )
            self.textboxes[i].setText(str(self._fiducial_views[i].xy))

        # Calculate stereoshift and depth
        self.shift_fiducial = length(self.f(1).xy, self.f(2).xy)
        self.shift_point = length(self.b(1).xy, self.b(2).xy)
        self.point_stereoshift = stereoshift(
            *[view.xy for view in self._fiducial_views]
        )
        self.point_depth = depth(
            self.f(1),
            self.f(2),
            self.b(1),
            self.b(2),
            reverse=self.cmb_ref_fiducial.currentIndex(),
        )
        self.spoints = self.cal_layer.data[1:]

        # Populate the table
        self.tshift_fiducial.setText(str(self.shift_fiducial))
        self.tshift_point.setText(str(self.shift_point))
        self.tstereoshift.setText(str(self.point_stereoshift))
        self.tdepth.setText(str(self.point_depth))

    def _on_click_save_to_table(self) -> None:
        """When 'Save to table' button is clicked, propagate stereoshift and depth to main table"""

        # Propagate to particle
        selected_row = self.parent._get_selected_row()
        self.parent.data[selected_row].spoints = self.spoints
        self.parent.data[selected_row].shift_fiducial = self.shift_fiducial
        self.parent.data[selected_row].shift_point = self.shift_point
        self.parent.data[selected_row].stereoshift = self.point_stereoshift
        self.parent.data[selected_row].depth_cm = self.point_depth

        # Propagate to parent table
        for i in range(2):
            self.parent.table.setItem(
                selected_row,
                self.parent._get_table_column_index("sf" + str(i + 1)),
                QTableWidgetItem(str(self.spoints[i])),
            )
            self.parent.table.setItem(
                selected_row,
                self.parent._get_table_column_index("sp" + str(i + 1)),
                QTableWidgetItem(str(self.spoints[i + 2])),
            )
        self.parent.table.setItem(
            selected_row,
            self.parent._get_table_column_index("shift_fiducial"),
            QTableWidgetItem(str(self.shift_fiducial)),
        )
        self.parent.table.setItem(
            selected_row,
            self.parent._get_table_column_index("shift_point"),
            QTableWidgetItem(str(self.shift_point)),
        )
        self.parent.table.setItem(
            selected_row,
            self.parent._get_table_column_index("stereoshift"),
            QTableWidgetItem(str(self.point_stereoshift)),
        )
        self.parent.table.setItem(
            selected_row,
            self.parent._get_table_column_index("depth_cm"),
            QTableWidgetItem(str(self.point_depth)),
        )

    def cancel(self) -> None:
        """On cancel remove the points_Stereoshift layer"""

        # TODO: this is a problem, the layer still exists... not sure how to remove it
        self.parent.viewer.layers.select_previous()
        self.parent.viewer.layers.remove(self.cal_layer)
        return super().accept()
