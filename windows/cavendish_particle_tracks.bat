:: This is an example batch file to run the python script start_cpt.py
:: The file start_cpt.py is a Python script that starts napari with the Cavendish Particle Tracks plugin
@echo off
if not exist "%userprofile%\.napari" mkdir  %userprofile%\.napari
set NUMBA_CACHE_DIR=%userprofile%\.napari
set CPT_SHUFFLING_SEED=1
:: napari -w cavendish-particle-tracks
python start_cpt.py
