
# Contributing

Contributions are very welcome.

Developers will need to checkout a development copy of the plugin and install it in editable mode.
Presumably also with the testing dependencies:

    git clone git@github.com/palvarezc/cavendish-particle-tracks.git
    cd cavendish-particle-tracks
    python -m pip install -e ".[testing]"


Tests are run with [tox] across python 3.9, 3.10, 3.11 and 3.12 (following [SPEC0](https://scientific-python.org/specs/spec-0000/#support-window)).
You can also check quickly with `pytest` if you installed the `testing` extras.
Please ensure the coverage at least stays the same before you submit a pull request.

We also use `pre-commit` to ensure uniform code style.

    python -m pip install pre-commit
    pre-commit run # before committing

[tox]: https://tox.readthedocs.io/en/latest/

## Contributing documentation
We are using the [myst](https://myst-parser.readthedocs.io/en/latest/index.html) markdown parser.

To test contributions to the documentation, this can be built locally following:

    python -m pip install -e ".[docs]"
    sphinx-build -W -b html docs docs/_build/html

Python's built in http server can be then used to serve the page:

    cd docs/_build/html
    python -m http.server

> [!NOTE]
> On macOS you can directly do `open docs/_build/html/index.html` to open the documentation in your browser.
