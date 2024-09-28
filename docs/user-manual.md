
# User's manual

## Introduction
The Cambridge Particle Tracks (CPT) tool has been developed for the analysis of tracks left by different particles in a bubble chamber detector. The tool is implemented as a [napari] plugin. [napari] is an open-source, multi-dimensional image viewer for Python, which allows the visualisation and analysis of multi-dimensional data. Our application is relatively simple, as we only use it to visualise 2D images, and we are not making use of the full capabilities of the library. To that end, the CPT plugin provides a simple and (hopefully) intuitive interface to interact with the data.

The CPT tool is designed to be used with the data from CERN's bubble chamber experiments that have been digitised and stored in the PartII Particle Tracks lab[^1]. The software allows the user to load and visualise the data, and to perform some basic analysis on the tracks. This manual describes how to use the tool to perform the measurements required for the practical.


## Usage

### Starting the tool

To start the tool, double-click on the CPT icon. This will open the `napari` window. To load the CPT plugin, click on the `Plugins` menu and select `cavendish-particle-tracks`. This will open the CPT window, which will be disabled until you load a data file.

### Loading a data file
To load a data file, click on the `Load data` button. This will open a file dialog, which will allow you to select the data folder you want to load. The data folder should have three subfolders corresponding to the three views of the detector. Each subfolder should contain the same number of images, one for each frame of the experiment.

In the Particle Tracks lab, the data is stored in the `CPT_data` folder. Please note that the images in the subfolders might not correspond to the view indicated in the folder name. You will need to check the images to determine which view they correspond to.

The data is loaded as a 4D array, with the dimensions corresponding to the event number, the view, the height and the width of the images. In practice, this means that once the data is loaded, the first view of the first frame will be displayed. The bottom sliders labelled `Event` and `Views` allow you to toggle between the different frames and different views for each frame, respectively.
The tool will also display the number of views and frames available, as well as the current view and frame.

### Adding a new particle
Once an interesting process is identified in the image, you can record information about that process. To start, you need to add a new particle decay to the table. To do this, click on the `New particle` button, and select the process you want to record.
This will create a new `ParticleDecay` object in the particle list, which will be displayed as a new entry in the table. This object will contain information about the particle decay, such as the type of decay and the event number and view in which you created it. Later, additional properties can be added (and modified) by the different measurement tools, so that you can record the relevant information about the particle decay.

### Measuring particle properties

Once a particle is added, you can measure its properties. To do this, select the particle from the particle list, as this will enable the tools correspondint to the measurements that can be performed. The properties that can be measured are:

- `Decay length`: The length of the particle path, between the origin and decay vertices.

- `Radius of curvature`: The radius of the circle that best fits the particle path.

- `Decay angles`: The angles between the particle path and its decay products. This measurement only makes sense for particles that decay into two visible products (i.e. {math}`\Lambda^0 \rightarrow p  \pi^-`).

- `Stereoshift`: The [stereoshift] is a proxy for the depth of the particle in the bubble chamber, see the Particle Tracks lab manual[^2] for details on the method. In this measurement two views of the same frame need to be examined.

#### Decay length
To measure the decay length, first select the particle you are making the measurement for in the particle list. Then, place and select two points in the `Radii and Lengths` layer, corresponding to the origin and decay vertex. Finally, click `Calculate length`. The distance between the two points is calculated and added to the selected particle. The length is show under the `decay_length` heading for the corresponding particle either in pixels or cm, depending on whether or not the `Apply magnification` option is selected.

#### Radius of curvature
To measure the radius of curvature, first select the particle you are making the measurement for in the particle list. Then, place and select three points along the particle trajectory in the `Radii and Lengths` layer. Finally, click `Calculate radius`. The radius of curvature is calculated and added to the selected particle. The radius is show under the `radius` heading for the corresponding particle either in pixels or cm, depending on whether or not the `Apply magnification` option is selected.

#### Decay angles
The measurement of the decay angles is only enabled for {math}`\Lambda^0 \to p \pi^-` decays. To start, select the particle you are making the measurement for in the particle list and click `Calculate decay angles`. This will open the `Decay Angles` menu and create a layer called `Decay Angles Tool` containing three lines, which will be labelled as the parent {math}`\Lambda^0` particle and the two decay products. Align each line with the corresponding particle trajectory and click `Calculate`. The angles between the {math}`\Lambda^0` and the proton and pion will be shown. Click `Save to table` to associate the angles to the selected particle in the particle list. The angles are shown under the `phi_proton` and `phi_pion` headings for the corresponding particle.

#### Stereoshift
To measure the stereoshift of any point of interest (POI) in the image, two different views of the same frame need to be examined.

To start, select the particle you are making the measurement for in the particle list. This will open a `Stereoshift` menu and create a layer called `Points_Stereoshift` containing a number of points to be placed in the image. At the top of the dialog, a drop-down menu allows you to define your POI as the `origin` or `decay` vertex of the corresponding particle.

For each steresoshift measurement, six points are placed in the image:
- Two `Reference` points, used to correct for the misalignment of the two views.
- Two `Fiducial` points, used to measure the fiducial stereoshift.
- Two `Point` points, used to measure the stereoshift of the POI.

By default, the `Reference` point is considered to be at the front of the chamber, while the `Fiducial` is considered to be at the back. However, a valid measurement can also be done with the opposite choice of positions. A drop-down menu allows you to select the front or back position for the reference and fiducial points. The default option is displayed as `Front/Back`.

Flicking between the two views, place the points on the corresponding reference and fiducial markings and the POI. Finally, click `Calculate `. The measurement of the calculated shift for the fiducial marking and POI is shown, together with the stereoshift and the depth of the POI measured from the front bubble chamber window. Click `Save to table` to associate the depth measurement to the selected particle in the particle list. The depth is shown under the `depth` heading for the corresponding particle in centimeters.

After each stereoshift measurement, the tool will remember position of the fiducial markings and the POI. This is useful if you need to measure the stereoshift for different points in the same region of the bubble chamber.

### Measuring the image magnification
In addition to the properties associated with a specific particle, the tool allows you to measure the image magnification. As explained in the lab manual[^2], this is done by measuring the projected distance between two pairs of fiducial markings, one at the front and one at the back window of the bubble chamber. To do this, click on the `Measure magnification` button. This will enable the magnification tool, and create a new layer called `Magnification`. Create one point for each of the fiducial markings in the image. To record them, select each point, identify it using the drop down menu in the dialog and click `Add`. Once you have placed all four points, click `Calculate magnification`. The tool will then calculate the magnification parameters which, combined with a measurement of the depth, can be used to convert the measurements of the particle properties to real dimensions in the detector.

Once computed for the first time, the magnification parameters are stored and used to convert all measurements. If you need to recompute the magnification parameters, you can do so by clicking on the `Update magnification` button. The tool will remember previously computed magnification parameters, and will allow you to switch between them.

### Saving the data
To save the data, click on the `Save to file` button. This will open a file dialog, which will allow you to select the file where you want to save the data. The tool will save the data in a CSV file, which will contain the information about the particles, and their properties, as well as the magnification parameters.

## Useful keyboard shortcuts
A number of keybindigs are available to make the use of the tool more efficient. For example, when a points layer is selected, the following keybindings are available:

- `P` or `2` will activate the `Add point` mode.
- `S` or `3` will activate the `Select/Move point` mode.
- `4` will activate the `Move layer` mode.

Hovering over the buttons in the dialog will show the corresponding keybinding.

## References
[^1]: For tests you can use the data stored in `/r01/ParticleTracks/real_data` on the HEP machines.

[^2]: Part II Particle Tracks lab manual, Cavendish Laboratory, 2024.

[napari]: https://napari.org/stable/
[stereoshift]: https://www.hep.phy.cam.ac.uk/~palvarez/ParticleTracks/
