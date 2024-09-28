
# User's manual

## Introduction
The Cambridge Particle Tracks (CPT) tool has been developed for the analysis of particle tracks in a detector. The tool is implemented as a [napari] plugin. [napari] is an open-source, multi-dimensional image viewer for Python, which allows the visualisation and analysis of multi-dimensional data. Our application is relatively simple, as we only use it to visualise 2D images, and we are not making use of the full capabilities of the library. To that end, the CPT plugin provides a simple and (hopefully) intuitive interface to interact with the data.

The CPT tool is designed to be used with the data from CERN bubble chamber experiments that have been digitised and stored in the PartII Particle Tracks lab[^1]. The software allows the user to load and visualise the data, and to perform some basic analysis on the tracks. This manual describes how to use the tool to perform the measurements required for the practical.


## Usage

### Starting the tool

To start the tool, double-click on the CPT icon. This will open the `napari` window. To load the CPT plugin, click on the `Plugins` menu and select `cavendish-particle-tracks`. This will open the CPT window, which will be empty until you load a data file.

### Loading a data file
To load a data file, click on the `Load data` button. This will open a file dialog, which will allow you to select the data folder you want to load. The data folder should have three subfolders corresponding to the three views of the detector. Each subfolder should contain the same number of images, one for each frame of the experiment.

In the Particle Tracks lab, the data is stored in the `CPT_data` folder. Please note that the images in the subfolders might not correspond to the view indicated in the folder name. You will need to check the images to determine which view they correspond to.

The data is loaded as a 4D array, with the dimensions corresponding to the views, the frames, the height and the width of the images. In practice, this means that once the data is loaded, the first view of the first frame will be displayed. The bottom sliders labelled `Event` and `Views` allow you to toggle between the different frames and different views for each frame, respectively.
The tool will also display the number of views and frames available, as well as the current view and frame.

### Adding a new particle
Once an interesting process is identified in the image, you can record information about that process. To start, you need to add a new particle. To do this, click on the `Add particle` button, and select the process you want to record.
This will create a new particle object in the particle list, which will be displayed as a new entry in the table [^2].

### Measuring particle properties

Once a particle is added, you can measure its properties. To do this, select the particle from the particle list, as this will enable the measurement that can be performed. The properties that can be measured are:

- `Decay length`: The length of the particle path, between the origin and decay vertices.

- `Radius of curvature`: The radius of the circle that best fits the particle path.

- `Decay angles`: The angles between the particle path and its decay products. This measurement only makes sense for particles that decay into two visible products (i.e. {math}`\Lambda^0 \rightarrow p  \pi^-`).

- `Stereoshift`: The [stereoshift] is a proxy for the depth of the particle in the bubble chamber, see the Particle Tracks lab manual[^3] for details on the method. In this measurement two views of the same frame need to be examined.

#### Decay length
To measure the decay length, first select the particle you are making the measurement for in the particle list. Then, place and select two points in the `Points` layer, corresponding to the origin and decay vertex. Finally, click `Calculate length`. The distance between the two points is calculated and added to the selected particle. The length is show under the `decay_length` heading for the corresponding particle either in pixels or cm, depending on whether or not the `Apply magnification` option is selected.

#### Radius of curvature
To measure the radius of curvature, first select the particle you are making the measurement for in the particle list. Then, place and select three points along the particle trajectory in the `Points` layer. Finally, click `Calculate radius`. The radius of curvature is calculated and added to the selected particle. The radius is show under the `radius` heading for the corresponding particle either in pixels or cm, depending on whether or not the `Apply magnification` option is selected.

#### Decay angles
The measurement of the decay angles is only enabled for {math}`\Lambda^0 \to p \pi^-` decays. To start, select the particle you are making the measurement for in the particle list and click `Calculate decay angles`. This will open the `Decay angles` menu and create a layer called `Decay angles tool` containing three lines, which will be labelled as the parent {math}`\Lambda^0` particle and the two decay products. Align each line with the corresponding particle trajectory and click `Calculate`. The angles between the {math}`\Lambda^0` and the proton and pion will be shown. Click `Save to table` to associate the angles to the selected particle in the particle list. The angles are shown under the `phi_proton` and `phi_pion` headings for the corresponding particle.

#### Stereoshift
To measure the stereoshift of any point of interest (POI) in the image, two different views of the same frame need to be examined[^4].

To start, select the particle you are making the measurement for in the particle list. This will open a `Stereoshift` menu and create a layer called `Points_Stereoshift` containing a number of points to be placed in the image. The points are labelled according to the view and whether they represent a `Front fiducial`, `Back fiducial` or POI point (`Point`). Flicking between the two views, place the points on the corresponding fiducial markings and the POI. Finally, click `Calculate `. The measurement of the calculated shift for the fiducial marking and POI is shown, together with the stereoshift and the depth of the POI measured from the front bubble chamber window[^5]. Click `Save to table` to associate the depth measurement to the selected particle in the particle list. The depth is shown under the `depth` heading for the corresponding particle in cm.

After each stereoshift measurement, the tool will remember position of the fiducial markings and the POI. This is useful if you need to measure the stereoshift for different points in the same region of the bubble chamber.

### Measuring the image magnification
In addition to the properties associated with a specific particle, the tool allows you to measure the image magnification. As explained in the lab manual[^3], this is done by measuring the projected distance between two pairs of fiducial markings, one at the top and one at the bottom of the bubble chamber. To do this, click on the `Measure magnification` button. This will enable the magnification tool, which will ask you to select and identify four fiducial positions in the image. The tool will then calculate the magnification parameters, which, combined with a measurement of the depth, can be used to convert the measurements of the particle properties to real units.

Once computed for the first time, the magnification parameters are stored and used to convert all measurements. If you need to recompute the magnification parameters, you can do so by clicking on the `Measure magnification` button again. The tool will remember previously computed magnification parameters, and will allow you to switch between them.

### Saving the data
The data is stored internally as a list of `ParticleDecays` objects, which contain the information about the particles, their properties, as well as the magnification parameters.

To save the data to a file for the analysis, click on the `Save to file` button. This will open a file dialog, which will allow you to select the file where you want to save the data. Two file types are suported: `CSV` and `Pickle`.

The `CSV` file will save the data in a human-readable format, which can be opened in a text editor or a spreadsheet program. Make sure to import the data as a CSV file with the correct delimiter (`,`) and the right encoding (`UTF8`) so that the symbols are rendered correctly.

The `Pickle` file will save the data in a binary format, which can be open with Python using:

    ```python
    import pickle
    with open('filename.pkl', 'rb') as f:
        data = pickle.load(f)
    ```

The measurements associated with each particle can be accessed by interrogating the elements of `data`:

    ```python
    >> print("Decay 0 is: ", data[0].name)
    Decay 0 is:  Σ⁺ ⇨ n + π⁺
    >> print("The decay length of Decay 0 is: ", data[0].decay_length_cm, "cm")
    The decay length of Decay 0 is:  0.55 cm
    ```

This can be useful if you want to perform the analysis in Python or Jupyter notebooks.
## Useful keyboard shortcuts
Some tips...

## References
[^1]:For tests you can use the data stored in `/r01/ParticleTracks/real_data` on the HEP machines.

[^2]: Showing particle ID and the frame where the particle is located.

[^3]: Particle Tracks lab manual, 2024.

[^4]: Realised that for the measurement of the {math}`\Lambda^0` students are asked to measure the stereoshift for both the origin and decay vertex, to obtain the total decay lenth. At the moment this is not possible with the tool, as it only allows to measure the stereoshift for a single point. Need to think how to implement this, or work around it.

[^5]: Understand if the Back/Front option is now obsolete.

[napari]: https://napari.org/stable/
[stereoshift]: https://www.hep.phy.cam.ac.uk/~palvarez/ParticleTracks/
