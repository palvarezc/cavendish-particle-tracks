from typing import Tuple

import numpy as np

Point = Tuple[float, float]


class Fiducial:
    def __init__(self, name="", x=-1.0e6, y=-1.0e6):
        self.name = name
        self.x = x
        self.y = y


BCdepth = 31.6

FIDUCIAL_FRONT = {
    "C’": [0.0, 0.0, 0.0],
    "F’": [14.97, -8.67, 0.0],
    "B’": [15.00, 8.66, 0.0],
    "D’": [29.91, -0.07, 0.0],
}  # cm
FIDUCIAL_BACK = {
    "C": [-0.02, 0.01, 31.6],
    "F": [14.95, -8.63, 31.6],
    "B": [14.92, 8.67, 31.6],
    "D": [29.90, 0.02, 31.6],
    "E": [-14.96, -8.62, 31.6],
    "A": [-15.00, 8.68, 31.6],
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


def magnification(f1, f2, b1, b2):
    a = 1.0
    b = 1.0
    return a, b
