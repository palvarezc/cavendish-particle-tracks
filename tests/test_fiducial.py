from cavendish_particle_tracks._calculate import Fiducial


def test_create_fiducial_point():
    p1 = Fiducial("D")
    p1.xy = (1.0, 2.0)
    assert p1.x == 1.0
    assert p1.y == 2.0
