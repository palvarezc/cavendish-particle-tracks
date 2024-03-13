from cavendish_particle_tracks._decay_angles_dialog import DecayAnglesDialog
from cavendish_particle_tracks._widget import ParticleTracksWidget


def test_decay_angles_dialog(make_napari_viewer, qtbot):
    """Smoke test for the DecayAnglesDialog."""
    my_widget = ParticleTracksWidget(make_napari_viewer())
    dialog = DecayAnglesDialog(parent=my_widget)
    qtbot.addWidget(dialog)

    # show dialog and check that it closes
    dialog.show()
    qtbot.waitForWindowShown(dialog)
    dialog.close()
    qtbot.waitSignals([dialog.rejected], timeout=5000)
