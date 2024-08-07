
# Contributing

Contributions are very welcome.

Developers will need to checkout a development copy of the plugin and install it in editable mode.
Presumably also with the testing dependencies:

    git clone git@github.com/samcunliffe/cavendish-particle-tracks.git
    cd cavendish-particle-tracks
    python -m pip install -e ".[testing]"


Tests are run with [tox] across python 3.8, 3.9, 3.10 and 3.11.
You can also check quickly with `pytest` if you installed the `testing` extras.
Please ensure the coverage at least stays the same before you submit a pull request.

We also use `pre-commit` to ensure uniform code style.

    python -m pip install pre-commit
    pre-commit run # before committing

Open PRs without a reviewer can be treated as a draft. When a reviewer is added this counts as ready for review.
(When open source we'll use proper drafts.)


[tox]: https://tox.readthedocs.io/en/latest/
