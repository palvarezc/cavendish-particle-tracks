# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Napari plugin for particle tracking analysis used in the Cavendish Laboratory's Undergraduate Part II Particle Tracks experiment. The plugin provides a GUI for analyzing bubble chamber particle decay images, including measurement of track radii, lengths, and angles.

## Common Development Commands

### Testing
- Run all tests: `pytest -v --color=yes --cov=cavendish_particle_tracks --cov-report=xml`
- Run specific test: `pytest tests/test_specific_file.py -v`
- Run with coverage: `pytest --cov=cavendish_particle_tracks`

### Code Quality
- Format code: `black .`
- Lint code: `ruff check .` (with auto-fix: `ruff check . --fix`)
- Type checking: `mypy src/cavendish_particle_tracks/`
- Run pre-commit hooks: `pre-commit run --all-files`

### Build and Install
- Install in development mode: `pip install -e .`
- Install with testing dependencies: `pip install -e .[testing]`
- Install with docs dependencies: `pip install -e .[docs]`
- Build documentation: Navigate to `docs/` and run `sphinx-build -b html . _build/html`

### Testing with tox
- Test across all Python versions: `tox`
- Test specific Python version: `tox -e py311`

## Architecture

### Core Components

**Main Widget (`_main_widget.py`)**
- `ParticleTracksWidget`: Primary GUI component that students interact with
- Contains table for particle decay data and analysis buttons
- Integrates with Napari viewer for image display and measurement tools

**Analysis Module (`analysis.py`)**
- Defines physical constants (chamber depth, fiducial positions)
- `ParticleDecay` dataclass: Core data structure for particle measurements
- `Fiducial` dataclass: Represents reference points in bubble chamber images
- Contains expected particle types and view definitions

**Calculation Functions (`_calculate.py`)**
- Physics calculations for track radius and length measurements
- Handles coordinate transformations and geometric computations

**Dialog Windows**
- `_magnification_dialog.py`: Calibration for image magnification
- `_stereoshift_dialog.py`: Stereo view alignment adjustments  
- `_decay_angles_dialog.py`: Angular measurements interface

### Data Flow
1. Images loaded into Napari viewer as `IMAGE_LAYER_NAME` layer
2. User makes measurements via Napari tools, stored in `MEASUREMENTS_LAYER_NAME` points layer
3. Measurements processed through calculation functions
4. Results displayed in main widget table
5. Data exportable to CSV for further analysis

### Key Constants
- `CHAMBER_DEPTH = 31.6` cm (physical bubble chamber depth)
- `FIDUCIAL_FRONT` and `FIDUCIAL_BACK`: Reference point coordinates
- `VIEW_NAMES = ["view1", "view2", "view3"]`: Stereo view identifiers
- `EXPECTED_PARTICLES`: List of particle decay types for analysis

## Development Notes

### Code Style
- Line length: 90 characters (Black formatter)
- Uses Ruff for linting with specific physics-related exceptions
- Type annotations required (mypy checking enabled)
- Pre-commit hooks enforce style consistency

### Testing Framework
- Uses pytest with Qt support (`pytest-qt`)
- Mock objects for Napari viewer interactions
- Coverage reporting via `pytest-cov`
- Test data in `tests/data/` directory

### Napari Integration
- Plugin manifest: `src/cavendish_particle_tracks/napari.yaml`
- Entry point: `ParticleTracksWidget` as main widget
- Depends on Napari 0.5.2+ but < 0.6.0 for layer controls compatibility

### Dependencies
- Core: `napari`, `numpy`, `dask-image`, `imagecodecs`
- GUI: QtPy (PyQt5/PySide2 abstraction)
- Testing: `pytest`, `pytest-qt`, `pytest-mock`, `pytest-cov`
- Development: `tox`, `black`, `ruff`, `mypy`, `pre-commit`