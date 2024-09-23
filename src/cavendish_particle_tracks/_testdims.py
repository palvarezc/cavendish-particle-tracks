from typing import TYPE_CHECKING

from skimage import data

if TYPE_CHECKING:
    from ._main_widget import ParticleTracksWidget

from qtpy.QtWidgets import QDialog


class TestDimsDialog(QDialog):
    def __init__(self, parent: "ParticleTracksWidget"):
        # Call parent constructor
        super().__init__(parent)

        # Declare instance variables + constants
        self.parent = parent

        blobs = data.binary_blobs(
            length=100, blob_size_fraction=0.05, n_dim=4, volume_fraction=0.05
        )

        parent.viewer.add_image(blobs.astype(float), name="Binary Blobs")

        parent.viewer.dims.axis_labels = ("View", "Event", "Y", "X")
        parent.viewer.dims.point = [0, 1, 0, 0]
        print("Done")
