import pytest
from cavendish_particle_tracks._calculate import radius


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
