:: This script will start napari with the Cavendish Particle Tracks plugin
:: Set the seed for shuffling the images (CPT_SHUFFLING_SEED) to a different value in each lab computer
:: Create a shortcut to this file and place it in the Public Desktop folder
:: If you are feeling creative, you can also change the icon of the shortcut to the Cavendish logo (C:\Program Files\Python39\Lib\site-packages\cavendish_particle_tracks\docs\ParticleCrocodile.png)
@echo off
if not exist "%userprofile%\.napari" mkdir  %userprofile%\.napari
set PYTHON_ROOT=C:\Program Files\Python39
set NUMBA_CACHE_DIR=%userprofile%\.napari
set CPT_SHUFFLING_SEED=1
:: napari -w cavendish-particle-tracks
python %PYTHON_ROOT%\Lib\site-packages\cavendish_particle_tracks\windows\start_cpt.py
