import numpy as np
from cavendish_particle_tracks import ParticleTracksWidget


def test_calculate_radius_ui(make_napari_viewer, capsys):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100)))

    # create our widget, passing in the viewer
    my_widget = ParticleTracksWidget(viewer)

    # need to click "new particle" to add a row to the table
    my_widget.cb.setCurrentIndex(1)
    my_widget._on_click_new_particle()

    # add three points to the points layer and select them
    viewer.add_points([(0, 1), (1, 0), (0, -1)])
    for layer in viewer.layers:
        if layer.name == "Points":
            layer.selected_data = {0, 1, 2}

    # click the calculate radius button
    my_widget._on_click_calculate()

    # read captured output and check that it's as we expected
    captured = capsys.readouterr()
    expected_lines = ["Adding points to the table:", "calculating radius!"]
    for expected in expected_lines:
        assert expected in captured.out


def test_selected_cells_workflow():
    assert True


def test_add_new_particle_ui(make_napari_viewer, capsys):
    viewer = make_napari_viewer()
    widget = ParticleTracksWidget(viewer)
    assert widget.table.rowCount() == 0

    widget.cb.setCurrentIndex(1)
    widget._on_click_new_particle()

    assert widget.table.rowCount() == 1
