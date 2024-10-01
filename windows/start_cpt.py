"""Start napari with the cavendish-particle-tracks plugin docked at the bottom

This script is intended to start `napari` with the plugin for use in the Cavendish lab computers.
"""

from napari import Viewer, run

from cavendish_particle_tracks import ParticleTracksWidget

viewer = Viewer()
plugin_docking_area = "bottom"

# Create the plugin
plugin_widget = ParticleTracksWidget(viewer, docking_area=plugin_docking_area)

# Add plugin to the viewer
dock_widget = viewer.window.add_dock_widget(
    plugin_widget, name="cavendish-particle-tracks", area=plugin_docking_area
)

run()
