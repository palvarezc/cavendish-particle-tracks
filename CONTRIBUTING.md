
# Contributing

Contributions are very welcome.

Developers will need to checkout a development copy of the plugin and install it in editable mode.
Presumably also with the testing dependencies:

    git clone git@github.com/palvarezc/cavendish-particle-tracks.git
    cd cavendish-particle-tracks
    python -m pip install -e ".[testing]"


Tests are run with [tox] across python 3.9, 3.10 and 3.11.
You can also check quickly with `pytest` if you installed the `testing` extras.
Please ensure the coverage at least stays the same before you submit a pull request.

We also use `pre-commit` to ensure uniform code style.

    python -m pip install pre-commit
    pre-commit run # before committing

Open PRs without a reviewer can be treated as a draft. When a reviewer is added this counts as ready for review.
(When open source we'll use proper drafts.)


[tox]: https://tox.readthedocs.io/en/latest/

## Contributing documentation
To test contributions to the documentation, this can be built locally following:

    python -m pip install ".[docs]"
    sphinx-build -W -b html docs docs/_build/html

Python's built in http server can be then used to serve the page:

    cd docs/_build/html
    python -m http.server
