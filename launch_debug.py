# launch this file in debug mode in your desired IDE with breakpoints added where relevant
# launch_napari.py
from napari import Viewer, run

viewer = Viewer()
dock_widget, plugin_widget = viewer.window.add_plugin_dock_widget(
    "cavendish-particle-tracks", "Cavendish Particle Tracks Analysis"
)

# or if you want it to dock somewhere
#dock_widget, plugin_widget = viewer.window.add_plugin_dock_widget("cavendish-particle-tracks", "Cavendish Particle Tracks Analysis")

# Manually set the dock widget's position to the bottom
#viewer.window.add_dock_widget(dock_widget, area='bottom')
# Optional steps to setup your plugin to a state of failure
# E.g. plugin_widget.parameter_name.value = "some value"
# E.g. plugin_widget.button.click()
run()
