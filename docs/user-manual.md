
# Cambridge Particle Tracks - User's manual

<!-- TOC start -->

- [Introduction](#introduction)
- [Usage](#usage)
    * [Starting the tool](#start)
    * [Loading the data](#load)
    * [Adding a new particle](#newparticle)
    * [Measuring particle properties](#measure)
        + [Decay length](#length)
        + [Radius of curvature](#radius)
        + [Decay angles](#angles)
        + [Stereoshift](#stereoshift)
    * [Measuring the image magnification](#magnification)
    * [Saving the data](#save)
- [Useful keyboard shortcuts](#tips)
- [References](#references)


<!-- TOC end -->

<!-- TOC --><a name="introduction"></a>
## Introduction
The Cambridge Particle Tracks (CPT) tool has been developed for the analysis of particle tracks in a detector. The tool is implemented as a [napari] plugin. [napari] is an open-source, multi-dimensional image viewer for Python, which allows the visualisation and analysis of multi-dimensional data. Our application is relatively simple, as we only use it to visualise 2D images, and we are not making use of the full capabilities of the library. To that end, the CPT plugin provides a simple and (hopefully) intuitive interface to interact with the data.

The CPT tool is designed to be used with the data from CERN bubble chamber experiments that have been digitised and stored in the PartII Particle Tracks lab[^1]. The software allows the user to load and visualise the data, and to perform some basic analysis on the tracks. This manual describes how to use the tool to perform the measurements required for the practical.


<!-- TOC --><a name="usage"></a>
## Usage

<!-- TOC --><a name="start"></a>
### Starting the tool

To start the tool, double-click on the CPT icon. This will open the `napari` window. To load the CPT plugin, click on the `Plugins` menu and select `cavendish-particle-tracks`. This will open the CPT window, which will be empty until you load a data file.

<!-- TOC --><a name="load"></a>
### Loading a data file
To load a data file, click on the `Load data` button. This will open a file dialog, which will allow you to select the data folder you want to load. The data folder should have three subfolders corresponding to the three views of the detector. Each subfolder should contain the same number of images, one for each frame of the experiment.

In the Particle Tracks lab, the data is stored in the `CPT_data` folder. Please note that the images in the subfolders might not correspond to the view indicated in the folder name. You will need to check the images to determine which view they correspond to.

The data is loaded as a 4D array, with the dimensions corresponding to the views, the frames, the height and the width of the images. In practice, this means that once the data is loaded, the first view of the first frame will be displayed. The bottom sliders labeled `Event` and `Views` allow you to toggle between the different frames and different views for each frame, respectively.
The tool will also display the number of views and frames available, as well as the current view and frame.

<!-- TOC --><a name="newparticle"></a>
### Adding a new particle
Once an interesting process is identified in the image, you can record information about that process. To start, you need to add a new particle. To do this, click on the `Add particle` button, and select the process you want to record.
This will create a new particle object in the particle list, which will be displayed as a new entry on the table [^2].

<!-- TOC --><a name="measure"></a>
### Measuring particle properties

Once a particle is added, you can measure its properties. To do this, select the particle from the particle list, as this will enable the measurement that can be performed. The properties that can be measured are:

- `Decay length`: The length of the particle path, between the origin and decay vertices.

- `Radius of curvature`: The radius of the circle that best fits the particle path.

- `Decay angles`: The angles between the particle path and its decay products. This measurement only makes sense for particles that decay into two visible products (i.e. $\Lambda^0 \rightarrow p  \pi^-$).

- `Stereoshift`: This is a proxy for the depth of the particle in the bubble chamber, see the Particle Tracks lab manual~\cite{cpt_lab_script} for details on the method. In this measurement two views of the same frame need to be examined.

<!-- TOC --><a name="length"></a>
#### Decay length

<!-- TOC --><a name="radius"></a>
#### Radius of curvature

<!-- TOC --><a name="angles"></a>
#### Decay angles

<!-- TOC --><a name="stereoshift"></a>
#### Stereoshift

<!-- TOC --><a name="magnification"></a>
### Measuring the image magnification
In addition to the properties associated with a specific particle, the tool allows you to measure the image magnification. As explained in the lab manual~\cite{cpt_lab_script}, this is done by measuring the projected distance between two pairs of fiducial markings, one at the top and one at the bottom of the bubble chamber. To do this, click on the `Measure magnification` button. This will enable the magnification tool, which will ask you to select and identify four fiducial positions in the image. The tool will then calculate the magnification parameters, which, combined with a measurement of the depth, can be used to convert the measurements of the particle properties to real units.

Once computed for the first time, the magnification parameters are stored and used to convert all measurements. If you need to recompute the magnification parameters, you can do so by clicking on the `Measure magnification` button again. The tool will remember previously computed magnification parameters, and will allow you to switch between them.

<!-- TOC --><a name="save"></a>
### Saving the data
To save the data, click on the `Save to file` button. This will open a file dialog, which will allow you to select the file where you want to save the data. The tool will save the data in a CSV file, which will contain the information about the particles, and their properties, as well as the magnification parameters.

<!-- TOC --><a name="tips"></a>
## Useful keyboard shortcuts
Some tips...

<!-- TOC --><a name="references"></a>
## References
[^1]:For tests you can use the data stored in `/r01/ParticleTracks/real_data` on the HEP machines.

[^2]: Showing particle ID and the frame where the particle is located.

[napari]: https://napari.org/stable/
[cpt_lab_script]: https://www.hep.phy.cam.ac.uk/~palvarez/ParticleTracks/
[def]: #stereoshift
