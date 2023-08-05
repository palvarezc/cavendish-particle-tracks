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

DATA_STRUCTURE = {
    "Type": "",
    "r1": [-1.0e6, -1.0e6],
    "r2": [-1.0e6, -1.0e6],
    "r3": [-1.0e6, -1.0e6],
    "radius": 0.0,
    "d1": [-1.0e6, -1.0e6],
    "d2": [-1.0e6, -1.0e6],
    "decay length": 0.0,
    "sf1": [-1.0e6, -1.0e6],
    "sf2": [-1.0e6, -1.0e6],
    "sp1": [-1.0e6, -1.0e6],
    "sp2": [-1.0e6, -1.0e6],
    "stereoshift": -1.0,
    "mag_a": -1.0,
    "mag_b": -1.0,
    "evtNumber": -1,
}


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
    name: str = ""
    r1: list[float] = field(default_factory=list)
    r2: list[float] = field(default_factory=list)
    r3: list[float] = field(default_factory=list)
    radius: float = 0.0
    d1: list[float] = field(default_factory=list)
    d2: list[float] = field(default_factory=list)
    decay_length: float = 0.0
    sf1: list[float] = field(default_factory=list)
    sf2: list[float] = field(default_factory=list)
    sp1: list[float] = field(default_factory=list)
    sp2: list[float] = field(default_factory=list)
    stereoshift: float = -1.0
    magnification_a: float = -1.0
    magnification_b: float = -1.0
    event_number: int = -1

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
        