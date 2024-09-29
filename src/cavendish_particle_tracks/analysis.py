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

VIEW_NAMES = ["view1", "view2", "view3"]

EXPECTED_PARTICLES = [
    "New particle",
    "Σ⁺ ⇨ p + π⁰",
    "Σ⁺ ⇨ n + π⁺",
    "Σ⁻ ⇨ n + π⁻",
    "Λ⁰ ⇨ p + π⁻",
    "Λ⁰ ⇨ n + π⁰",
]


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


# Idea is to save a list of ParticleDecays as we go along, and then pandas.DataFrame(list_of_particles) does all the magic
@dataclass
class ParticleDecay:
    name: str = ""
    index: int = 0
    _r1: list[float] = field(default_factory=lambda: [0.0, 0.0])
    _r2: list[float] = field(default_factory=lambda: [0.0, 0.0])
    _r3: list[float] = field(default_factory=lambda: [0.0, 0.0])
    radius_px: float = -1.0
    radius_cm: float = -1.0
    _d1: list[float] = field(default_factory=lambda: [0.0, 0.0])
    _d2: list[float] = field(default_factory=lambda: [0.0, 0.0])
    decay_length_px: float = -1.0
    decay_length_cm: float = -1.0
    _sf1: list[float] = field(default_factory=lambda: [0.0, 0.0])
    _sf2: list[float] = field(default_factory=lambda: [0.0, 0.0])
    _sp1: list[float] = field(default_factory=lambda: [0.0, 0.0])
    _sp2: list[float] = field(default_factory=lambda: [0.0, 0.0])
    shift_fiducial: Fiducial = field(default_factory=Fiducial)
    shift_point: Fiducial = field(default_factory=Fiducial)
    stereoshift: float = -1.0
    depth_cm: float = -1.0
    magnification_a: float = -1.0
    magnification_b: float = 0.0
    # magnification: float = -1.0
    phi_proton: float = -100
    phi_pion: float = -100
    event_number: int = -1
    view_number: int = -1

    def _vars_to_show(self, calibrated=False):
        if calibrated:
            return [
                "name",
                "radius_cm",
                "decay_length_cm",
                "depth_cm",
                "magnification",
                "phi_proton",
                "phi_pion",
            ]
        else:
            return [
                "name",
                "radius_px",
                "decay_length_px",
                "depth_cm",
                "magnification",
                "phi_proton",
                "phi_pion",
            ]

    def _vars_to_save(self):
        """Variable to save in the output file, all for the moment"""
        vars_to_save = [var for var in self.__dict__ if var[0] != "_"]
        vars_to_save += ["rpoints", "dpoints", "spoints"]
        return vars_to_save

    @property
    def rpoints(self):
        return [self._r1, self._r2, self._r3]

    @rpoints.setter
    def rpoints(self, values):
        for i, point in enumerate(self.rpoints):
            point[0] = values[i][0]
            point[1] = values[i][1]

    @property
    def dpoints(self):
        return [self._d1, self._d2]

    @dpoints.setter
    def dpoints(self, values):
        for i, point in enumerate(self.dpoints):
            point[0] = values[i][0]
            point[1] = values[i][1]

    @property
    def spoints(self):
        return [self._sf1, self._sf2, self._sp1, self._sp2]

    @spoints.setter
    def spoints(self, values):
        for i, point in enumerate(self.spoints):
            point[0] = values[i][0]
            point[1] = values[i][1]

    @property
    def magnification(self):
        return self.magnification_a + self.magnification_b * self.depth_cm

    def calibrate(self) -> None:
        self.radius_cm = self.magnification * self.radius_px
        self.decay_length_cm = self.magnification * self.decay_length_px

    def to_csv(self):
        mystring = ""
        for var in self._vars_to_save():
            mystring += str(getattr(self, var)) + ","
        return mystring[0:-1] + "\n"
