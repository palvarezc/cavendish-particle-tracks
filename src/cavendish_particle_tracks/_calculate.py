from typing import Tuple

import numpy as np

from cavendish_particle_tracks._analysis import (
    CHAMBER_DEPTH,
    FIDUCIAL_BACK,
    FIDUCIAL_FRONT,
    Fiducial,
)

Point = Tuple[float, float]


def radius(a: Point, b: Point, c: Point) -> float:
    lhs = np.array(
        [
            [2 * a[0], 2 * a[1], 1],
            [2 * b[0], 2 * b[1], 1],
            [2 * c[0], 2 * c[1], 1],
        ]
    )
    rhs = np.array(
        [
            a[0] * a[0] + a[1] * a[1],
            b[0] * b[0] + b[1] * b[1],
            c[0] * c[0] + c[1] * c[1],
        ]
    )
    xc, yc, k = np.linalg.solve(lhs, rhs)
    return np.sqrt(xc * xc + yc * yc + k)


def length(a: Point, b: Point) -> float:
    pa = np.array(a)
    pb = np.array(b)
    return np.linalg.norm(pa - pb)


def magnification(f1: Fiducial, f2: Fiducial, b1: Fiducial, b2: Fiducial):
    # (Delta t)/(Delta p) = a + b*z
    tf1 = np.array(FIDUCIAL_FRONT[f1.name])
    tf2 = np.array(FIDUCIAL_FRONT[f2.name])
    tb1 = np.array(FIDUCIAL_BACK[b1.name])
    tb2 = np.array(FIDUCIAL_BACK[b2.name])

    a = np.linalg.norm(tf1 - tf2) / np.linalg.norm(f1.xy - f2.xy)
    b = (
        np.linalg.norm(tb1 - tb2) / np.linalg.norm(b1.xy - b2.xy) - a
    ) / CHAMBER_DEPTH

    return a, b


def stereoshift(fa: Point, fb: Point, pa: Point, pb: Point):
    # stereoshift = (Delta p)/(Delta f)
    nfa = np.array(fa)
    nfb = np.array(fb)
    npa = np.array(pa)
    npb = np.array(pb)

    return np.linalg.norm(npa - npb) / np.linalg.norm(nfa - nfb)


def depth(f: Fiducial, fa: Point, fb: Point, pa: Point, pb: Point):
    # depth_p = (Delta p)/(Delta f) * depth_f
    depth_f = 0.0 if f.name in FIDUCIAL_FRONT else CHAMBER_DEPTH
    depth_p = stereoshift(fa, fb, pa, pb) * depth_f

    return depth_p
