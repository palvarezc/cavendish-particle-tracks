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

    def __str__(self):
        return f"Fiducial(name={self.name}; x={self.x}; y={self.y})"

    @property
    def xy(self):
        return np.array([self.x, self.y])

    @xy.setter
    def xy(self, point):
        self.x = point[0]
        self.y = point[1]


@dataclass
class StereoshiftInfo:
    name: str = ""
    sf1: list[float] = field(default_factory=list)
    sf2: list[float] = field(default_factory=list)
    sp1: list[float] = field(default_factory=list)
    sp2: list[float] = field(default_factory=list)
    shift_fiducial: float = 0.0
    shift_point: float = 0.0
    stereoshift: float = -1.0
    depth_cm: float = 0.0

    @property
    def spoints(self):
        return np.array([self.sf1, self.sf2, self.sp1, self.sp2])

    @spoints.setter
    def spoints(self, points):
        self.sf1, self.sf2, self.sp1, self.sp2 = points

    def __str__(self):
        return f"StereoshiftInfo(name={self.name}; sf1={self.sf1}; sf2={self.sf2}; sp1={self.sp1}; sp2={self.sp2}; shift_fiducial={self.shift_fiducial}; shift_point={self.shift_point}; stereoshift={self.stereoshift}; depth_cm={self.depth_cm})"


# Idea is to save a list of ParticleDecays as we go along, and then pandas.DataFrame(list_of_particles) does all the magic
@dataclass
class ParticleDecay:
    name: str = ""
    index: int = 0
    r1: list[float] = field(default_factory=list)
    r2: list[float] = field(default_factory=list)
    r3: list[float] = field(default_factory=list)
    radius_px: float = 0.0
    radius_cm: float = 0.0
    d1: list[float] = field(default_factory=list)
    d2: list[float] = field(default_factory=list)
    decay_length_px: float = 0.0
    decay_length_cm: float = 0.0
    magnification_a: float = -1.0
    magnification_b: float = 0.0
    origin_vertex_stereoshift_info: StereoshiftInfo = field(
        default_factory=StereoshiftInfo
    )
    decay_vertex_stereoshift_info: StereoshiftInfo = field(
        default_factory=StereoshiftInfo
    )
    phi_proton: float = -100
    phi_pion: float = -100
    event_number: int = -1
    view_number: int = -1

    def vars_to_show(self, calibrated=False):
        if calibrated:
            return [
                "name",
                "radius_cm",
                "decay_length_cm",
                "origin_vertex_depth_cm",
                "decay_vertex_depth_cm",
                "magnification",
                "phi_proton",
                "phi_pion",
            ]
        else:
            return [
                "name",
                "radius_px",
                "decay_length_px",
                "origin_vertex_depth_cm",
                "decay_vertex_depth_cm",
                "magnification",
                "phi_proton",
                "phi_pion",
            ]

    def vars_to_save(self):
        """Variable to save in the output file, all for the moment"""
        # return self.__dict__.keys()
        return list(self.__dict__.keys()) + [
            "origin_vertex_depth_cm",
            "decay_vertex_depth_cm",
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
    def origin_vertex_depth_cm(self):
        return self.origin_vertex_stereoshift_info.depth_cm

    @property
    def decay_vertex_depth_cm(self):
        return self.decay_vertex_stereoshift_info.depth_cm

    @property
    def average_depth_cm(self):
        return self.origin_vertex_stereoshift_info.depth_cm

    @property
    def magnification(self):
        return (
            self.magnification_a + self.magnification_b * self.average_depth_cm
        )

    def calibrate(self) -> None:
        self.radius_cm = self.magnification * self.radius_px
        self.decay_length_cm = self.magnification * self.decay_length_px

    def to_csv(self):
        mystring = ""
        for var in self.vars_to_save():
            mystring += str(getattr(self, var)) + ","
        return mystring[0:-1] + "\n"
