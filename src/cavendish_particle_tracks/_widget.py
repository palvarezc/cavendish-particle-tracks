"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

import napari
from qtpy.QtWidgets import QPushButton, QTableWidget, QVBoxLayout, QWidget


class ParticleTracksWidget(QWidget):
    """Widget containing a simple table of points and track radii per image."""

    def __init__(self, napari_viewer: napari.viewer.Viewer):
        super().__init__()
        self.viewer = napari_viewer

        # define QtWidgets
        cal = QPushButton("Calculate radius")
        ptc = QPushButton("New particle")
        self.table = self._set_up_table()

        # connect callbacks
        cal.clicked.connect(self._on_click_calculate)
        ptc.clicked.connect(self._on_click_new_particle)
        # TODO: find which of thsese works
        # https://napari.org/stable/gallery/custom_mouse_functions.html
        # self.viewer.mouse_press.callbacks.connect(self._on_mouse_press)
        # self.viewer.events.mouse_press(self._on_mouse_click)

        # layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.table)
        self.layout().addWidget(cal)
        self.layout().addWidget(ptc)

    def _set_up_table(self) -> QTableWidget:
        """Initial setup of the QTableWidget with one row and columns for each
        point and the calculated radius.
        """
        out = QTableWidget(1, 4)
        out.setHorizontalHeaderLabels(["1", "2", "3", "radius"])
        return out

    def _on_mouse_press(self) -> None:
        """When the mouse is clicked, record the cursor position."""
        print("clicked!")
        # layer.world_to_data(viewer.cursor.position)

    def _on_click_calculate(self) -> None:
        """When the 'Calculate radius' button is clicked, calculate the radius
        for the currently selected table row.
        """
        print("calculating radius!")

    def _on_click_new_particle(self) -> None:
        """When the 'New particle' button is clicked, append a new blank row to
        the table and select the first cell ready to recieve the first point.
        """
        print("napari has", len(self.viewer.layers), "layers")
