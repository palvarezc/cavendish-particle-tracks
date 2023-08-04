from typing import Tuple

import numpy as np

Point = Tuple[float, float]


class Fiducial:
    def __init__(self, name="", x=-1.0e6, y=-1.0e6):
        self.name = name
        self.x = x
        self.y = y


CHAMBER_DEPTH = 31.6

FIDUCIAL_FRONT = {
    "C'": [0.0, 0.0],
    "F'": [14.97, -8.67],
    "B'": [15.00, 8.66],
    "D'": [29.91, -0.07],
}  # cm
FIDUCIAL_BACK = {
    "C": [-0.02, 0.01],
    "F": [14.95, -8.63],
    "B": [14.92, 8.67],
    "D": [29.90, 0.02],
    "E": [-14.96, -8.62],
    "A": [-15.00, 8.68],
}  # cm


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
    pf1 = np.array([f1.x, f1.y])

    tf2 = np.array(FIDUCIAL_FRONT[f2.name])
    pf2 = np.array([f2.x, f2.y])

    tb1 = np.array(FIDUCIAL_BACK[b1.name])
    pb1 = np.array([b1.x, b1.y])

    tb2 = np.array(FIDUCIAL_BACK[b2.name])
    pb2 = np.array([b2.x, b2.y])

    a = np.linalg.norm(tf1 - tf2) / np.linalg.norm(pf1 - pf2)
    b = (
        np.linalg.norm(tb1 - tb2) / np.linalg.norm(pb1 - pb2) - a
    ) / CHAMBER_DEPTH

    return a, b
