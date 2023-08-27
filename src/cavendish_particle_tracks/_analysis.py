from dataclasses import dataclass, field

import numpy as np

CHAMBER_DEPTH = 31.6  # cm

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

EXPECTED_PARTICLES = ["New particle", "Σ+", "Σ-", "Λ0"]


@dataclass
class Fiducial:
    name: str = ""
    x: float = -1.0e6
    y: float = -1.0e6

    @property
    def xy(self):
        return np.array([self.x, self.y])

    @xy.setter
    def xy(self, point):
        self.x = point[0]
        self.y = point[1]


# Idea is to save a list of NewParticles as we go along, and then pandas.DataFrame(list_of_new_particles) does all the magic
@dataclass
class NewParticle:
    Name: str = ""
    r1: list[float] = field(default_factory=list)
    r2: list[float] = field(default_factory=list)
    r3: list[float] = field(default_factory=list)
    radius_px: float = 0.0
    radius_cm: float = 0.0
    d1: list[float] = field(default_factory=list)
    d2: list[float] = field(default_factory=list)
    decay_length_px: float = 0.0
    decay_length_cm: float = 0.0
    sf1: list[float] = field(default_factory=list)
    sf2: list[float] = field(default_factory=list)
    sp1: list[float] = field(default_factory=list)
    sp2: list[float] = field(default_factory=list)
    shift_fiducial: Fiducial = field(default_factory=Fiducial)
    shift_point: Fiducial = field(default_factory=Fiducial)
    stereoshift: float = -1.0
    depth_cm: float = 0.0
    magnification_a: float = -1.0
    magnification_b: float = 0.0
    # magnification: float = -1.0
    event_number: int = -1
    phi_proton: float = -100
    phi_pion: float = -100

    def _vars_to_show(self, calibrated=False):
        if calibrated:
            return [
                "Name",
                "radius_cm",
                "decay_length_cm",
                "depth_cm",
                "magnification",
                "phi_proton",
                "phi_pion",
            ]
        else:
            return [
                "Name",
                "radius_px",
                "decay_length_px",
                "depth_cm",
                "magnification",
                "phi_proton",
                "phi_pion",
            ]

    @property
    def rpoints(self):
        return np.array([self.r1, self.r2, self.r3])

    @rpoints.setter
    def rpoints(self, points):
        self.r1, self.r2, self.r3 = points

    @property
    def dpoints(self):
        return np.array([self.d1, self.d2])

    @dpoints.setter
    def dpoints(self, points):
        self.d1, self.d2 = points

    @property
    def spoints(self):
        return np.array([self.sf1, self.sf2, self.sp1, self.sp2])

    @spoints.setter
    def spoints(self, points):
        self.sf1, self.sf2, self.sp1, self.sp2 = points

    @property
    def magnification(self):
        return self.magnification_a + self.magnification_b * self.depth_cm

    def calibrate(self) -> None:
        self.radius_cm = self.magnification * self.radius_px
        self.decay_length_cm = self.magnification * self.decay_length_px
