from math import sqrt

import pytest
from cavendish_particle_tracks._calculate import length, radius


@pytest.mark.parametrize(
    "a, b, c, R",
    [
        ((0, 1), (1, 0), (0, -1), 1),
        ((-6, 3), (-3, 2), (0, 3), 5),
        ((1, 1), (2, 2), (3, 4), 5.7),
    ],
)
def test_calculate_radius(a, b, c, R):
    assert radius(a, b, c) == pytest.approx(R, rel=1e-3)


@pytest.mark.parametrize(
    "a, b, L",
    [
        ((0, 1), (1, 0), sqrt(2)),
        ((-3, 3), (-3, 2), 1),
        ((1, 1), (3, 4), sqrt(4 + 9)),
    ],
)
def test_calculate_length(a, b, L):
    assert length(a, b) == pytest.approx(L, rel=1e-3)
