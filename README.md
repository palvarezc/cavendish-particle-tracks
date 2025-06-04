# cavendish-particle-tracks

<p align="center"><img src="./docs/ParticleCrocodile.png" width=300 /></p>

[![License MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/samcunliffe/cavendish-particle-tracks/raw/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12|%203.13-blue)](https://python.org)
[![SPEC 0 — Minimum Supported Dependencies](https://img.shields.io/badge/SPEC-0-green?labelColor=%23004811&color=%235CA038)](https://scientific-python.org/specs/spec-0000/)
[![ci](https://github.com/palvarezc/cavendish-particle-tracks/workflows/ci/badge.svg)](https://github.com/palvarezc/cavendish-particle-tracks/actions)
[![codecov](https://codecov.io/github/palvarezc/cavendish-particle-tracks/graph/badge.svg?token=9R8IVMJT90)](https://codecov.io/github/palvarezc/cavendish-particle-tracks)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v0.json)](https://github.com/charliermarsh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
<!---
[![Python Version](https://img.shields.io/pypi/pyversions/cavendish-particle-tracks.svg?color=green)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/cavendish-particle-tracks.svg?color=green)](https://pypi.org/project/cavendish-particle-tracks)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/cavendish-particle-tracks)](https://napari-hub.org/plugins/cavendish-particle-tracks)
-->
----------------------------------

A Napari plugin to perform a simple particle tracking analysis for the Cavendish laboratory's Undergraduate Part II Particle Tracks experiment.

----------------------------------

## Installation

Firstly, you'll need to [install napari](https://napari.org/stable/tutorials/fundamentals/installation.html) following their latest instructions.

Then you can install this plugin with:

    python -m pip install git+https://github.com/palvarezc/cavendish-particle-tracks.git@v1.0.2

The version for 2024 students is [v1.0.2](https://github.com/palvarezc/cavendish-particle-tracks/releases).

> [!NOTE]
> On macOS we've found it easier to install napari through `conda-forge` (the napari docs give instructions for this under the **'From conda-forge using conda'** tab.)
> The Cavendish Particle tracks plugin can still be installed via `pip`, from inside your `conda` environment.

## Getting started

The user manual can be found [here](https://palvarezc.github.io/cavendish-particle-tracks/user-manual.html).

## License

Distributed under the terms of the [MIT] license,
"cavendish-particle-tracks" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin
[file an issue]: https://github.com/samcunliffe/cavendish-particle-tracks/issues
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
