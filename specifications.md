# Specifications

## Executive summary

> **Note**
> This [Napari](https://napari.org) plugin is to assist the analysis of digitally scanned frames from CERN bubble-chamber photographic data.
> It will be used to supplement the Cavendish Laboratory Cambridge Part II Physics Practicals.

## Statement of need

xxx

## Input data

The software must be able to open and analyse .tiff format greyscale files.
The are many such frames (O(1000)) of many event data, the software must be able to scan through the frames with 'forward' and 'backward' buttons.
That is: there should not be a long chain of user actions to open the next frame.
Each student would be expected to analyse O(10) frames in their analysis.

## Analysis requirements

The analysis of each frame is the measurement of the radii of several particle tracks left in the bubble chamber images.
The radii are measured by the coordinates of three points on the curved track.

## Software requirements

The software must run on linux machines provided by the laboratory and MacOS laptops of the demonstrators.

**The software is not required to run on Microsoft Windows.**


### Consequences of software failure

* Poor feedback from students.
* Wasted undergraduate laboratory time.
* Assessment difficulties.
