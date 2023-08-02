# cavendish-particle-tracks

[![License MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/samcunliffe/cavendish-particle-tracks/raw/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)](https://python.org)
[![ci](https://github.com/samcunliffe/cavendish-particle-tracks/workflows/ci/badge.svg)](https://github.com/samcunliffe/cavendish-particle-tracks/actions)
[![codecov](https://codecov.io/gh/samcunliffe/cavendish-particle-tracks/branch/main/graph/badge.svg?token=9R8IVMJT90)](https://codecov.io/gh/samcunliffe/cavendish-particle-tracks)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v0.json)](https://github.com/charliermarsh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
<!---
[![Python Version](https://img.shields.io/pypi/pyversions/cavendish-particle-tracks.svg?color=green)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/cavendish-particle-tracks.svg?color=green)](https://pypi.org/project/cavendish-particle-tracks)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/cavendish-particle-tracks)](https://napari-hub.org/plugins/cavendish-particle-tracks)
-->
----------------------------------

A Napari plugin to perform a simple particle tracking analysis for the Cavendish laboratory's Undergraduate Part II Particle Tracks experiment.

----------------------------------

## Installation

Firstly, you'll need to [install napari](https://napari.org/stable/tutorials/fundamentals/installation.html).

Then you can install this plugin with:

    pip install git+https://github.com/samcunliffe/cavendish-particle-tracks.git


## Getting started

**TODO** put some instructions with screenshots here.

## Contributing

Contributions are very welcome.

Developers will need to checkout a development copy of the plugin and install it in editable mode.
Presumably also with the testing dependencies:

    git clone git@github.com/samcunliffe/cavendish-particle-tracks.git
    cd cavendish-particle-tracks
    python -m pip install -e ".[testing]"


Tests are run with [tox] across python 3.8, 3.9, and 3.10.
You can also check quickly with `pytest` if you installed the `testing` extras.
Please ensure the coverage at least stays the same before you submit a pull request.

We also use `pre-commit` to ensure uniform code style.

    python -m pip install pre-commit
    pre-commit run # before committing

Open PRs without a reviewer can be treated as a draft. When a reviewer is added this counts as ready for review.
(When open source we'll use proper drafts.)

## License

Distributed under the terms of the [MIT] license,
"cavendish-particle-tracks" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/samcunliffe/cavendish-particle-tracks/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
