import yt
import yt.extensions.geotiff

from yt.data_objects.selection_objects.region import YTRegion

from yt_geotiff.testing import requires_file

land_use_data = "200km_2p5m_N38E34/200km_2p5m_N38E34.TIF"

@requires_file(land_use_data)
def test_rectangular_exceed_extents():
    ds = yt.load(land_use_data)
    width = ds.quan(2000., 'm')
    height = ds.quan(2000.,'m')
    rectangle_centre = ds.arr([3444202,3722218],'m')

    rectangular_yt_container = ds.rectangle_from_center(rectangle_centre, width, height)
    rectangular_yt_container[('bands','1')]

    assert isinstance(rectangular_yt_container, YTRegion)
