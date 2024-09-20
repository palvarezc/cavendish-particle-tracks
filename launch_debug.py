# launch this file in debug mode in your desired IDE with breakpoints added where relevant
# launch_napari.py
from napari import Viewer, run

from cavendish_particle_tracks._main_widget import ParticleTracksWidget

viewer = Viewer()
plugin_docking_area = "bottom"

# Create the plugin
plugin_widget = ParticleTracksWidget(
    viewer, bypass_load_screen=True, docking_area=plugin_docking_area
)

# Add plugin to the viewer
dock_widget = viewer.window.add_dock_widget(
    plugin_widget, name="cavendish-particle-tracks", area=plugin_docking_area
)

run()
