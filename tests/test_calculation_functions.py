from math import sqrt

import numpy as np
import pytest

from cavendish_particle_tracks._calculate import CHAMBER_DEPTH as CD
from cavendish_particle_tracks._calculate import FIDUCIAL_BACK as FB
from cavendish_particle_tracks._calculate import FIDUCIAL_FRONT as FF
from cavendish_particle_tracks._calculate import (
    angle,
    depth,
    length,
    magnification,
    radius,
    stereoshift,
)
from cavendish_particle_tracks.analysis import Fiducial


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


@pytest.mark.parametrize(
    "f1, f2, b1, b2, M",
    [
        (
            Fiducial("C'", *FF["C'"]),
            Fiducial("F'", *FF["F'"]),
            Fiducial("C", *FB["C"]),
            Fiducial("F", *FB["F"]),
            (1, 0),
        ),
        (
            Fiducial("C'", *np.multiply(2, FF["C'"])),
            Fiducial("F'", *np.multiply(2, FF["F'"])),
            Fiducial("C", *np.multiply(2, FB["C"])),
            Fiducial("F", *np.multiply(2, FB["F"])),
            (0.5, 0),
        ),
        (
            Fiducial("C'", *np.multiply(2, FF["C'"])),
            Fiducial("F'", *np.multiply(2, FF["F'"])),
            Fiducial("C", *np.divide(FB["C"], 0.5 + 0.3 * CD)),
            Fiducial("F", *np.divide(FB["F"], 0.5 + 0.3 * CD)),
            (0.5, 0.3),
        ),
    ],
)
def test_calculate_magnification(f1, f2, b1, b2, M):
    a, b = magnification(f1, f2, b1, b2)
    assert a == pytest.approx(M[0], rel=1e-3)
    assert b == pytest.approx(M[1], rel=1e-3)


@pytest.mark.parametrize(
    "f1, f2, p1, p2, S",
    [
        ((0, 1), (1, 0), (0, 0.5), (0.5, 0), 0.5),
        ((0, 0), (2, 2), (-1, 0), (0, -1), 0.5),
    ],
)
def test_calculate_stereoshift(f1, f2, p1, p2, S):
    assert stereoshift(f1, f2, p1, p2) == pytest.approx(S, rel=1e-3)


@pytest.mark.parametrize(
    "f1, f2, p1, p2, S",
    [
        (
            Fiducial("C", 0, 1),
            Fiducial("C", 1, 0),
            Fiducial("Point_view1", 0, 0.5),
            Fiducial("Point_view2", 0.5, 0),
            0.5 * CD,
        ),
        (
            Fiducial("C", 0, 0),
            Fiducial("C", 2, 2),
            Fiducial("Point_view1", -1, 0),
            Fiducial("Point_view2", 0, -1),
            0.5 * CD,
        ),
    ],
)
def test_calculate_depth(f1, f2, p1, p2, S):
    assert depth(f1, f2, p1, p2) == pytest.approx(S, rel=1e-3)
    assert depth(f1, f2, p1, p2, reverse=True) == pytest.approx(S, rel=1e-3)


@pytest.mark.parametrize(
    "v1, v2, theta12",
    [
        ([[-1, 1], [0, 0]], [[0, 0], [1, 0]], np.pi / 4),
        ([[-1, 1], [0, 0]], [[0, 0], [0, -1]], -1 * np.pi / 4),
        (
            [[1, -1], [0, 0]],
            [[0, 0], [1, 0]],
            -3 * np.pi / 4,
        ),
        ([[1, -1], [0, 0]], [[0, 0], [0, -1]], +3 * np.pi / 4),
    ],
)
def test_calculate_angles(v1, v2, theta12):
    assert angle(v1, v2) == pytest.approx(theta12, rel=1e-6)
