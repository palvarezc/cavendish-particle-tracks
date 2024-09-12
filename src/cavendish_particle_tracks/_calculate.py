import numpy as np

from ._analysis import (
    CHAMBER_DEPTH,
    FIDUCIAL_BACK,
    FIDUCIAL_FRONT,
    Fiducial,
)

Point = tuple[float, float]


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


def corrected_shift(points: list[Fiducial], offsets: list[Fiducial]) -> float:
    """Calculates the distance between two points, correcting for the offset/movement of the plane between two images.
    Points = Fiducial[]: The two points to calculate the distance between.
    Offsets = Fiducial[]: The two points to correct the distance calculation. (A fiducial in the reference plane)
    """
    # TODO: Improve docstring here.
    # Bodge a fix here till we come up with a better approach
    for i in range(len(points)):
        points[i].x -= offsets[i].x
        points[i].y -= offsets[i].y
    a = (points[0].x, points[0].y)
    b = (points[1].x, points[1].y)
    return length(a, b)


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


def depth(
    fa: Fiducial,
    fb: Fiducial,
    pa: Fiducial,
    pb: Fiducial,
    reverse: bool = False,
):
    if reverse:
        # depth_p = (1 - (Delta p)/(Delta f)) * depth_f
        return (1 - stereoshift(fa.xy, fb.xy, pa.xy, pb.xy)) * CHAMBER_DEPTH
    else:
        # depth_p = (Delta p)/(Delta f) * depth_f
        return stereoshift(fa.xy, fb.xy, pa.xy, pb.xy) * CHAMBER_DEPTH


def track_parameters(line):
    slope = (line[0][1] - line[1][1]) / (line[0][0] - line[1][0])
    intercept = line[0][1] - slope * line[0][0]
    return slope, intercept


def angle(line1: np.array, line2: np.array) -> float:
    v1, v2 = np.diff(line1, axis=0)[0], np.diff(line2, axis=0)[0]
    return np.arccos(
        np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    )
