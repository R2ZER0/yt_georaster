import os
import yt
import yt.extensions.geotiff

from yt.data_objects.selection_objects.region import YTRegion

from yt_geotiff.testing import get_path, requires_file

s2_data_1 = "Sentinel-2_sample_L2A/T30UVG_20200601T113331_B02_20m.jp2"
s2_data_2 = "Sentinel-2_sample_L2A/T30UVG_20200601T113331_B01_60m.jp2"
@requires_file(s2_data_1)
@requires_file(s2_data_2)
def test_rectangular():
    fns = get_path([s2_data_1, s2_data_2])
    ds = yt.load(*fns)
    width = ds.quan(500., 'm')
    height = ds.quan(500.,'m')
    rectangle_centre = ds.arr([473951,6155327],'m')
    rectangular_yt_container = ds.rectangle_from_center(rectangle_centre,width,height)
    rectangular_yt_container[('bands','S2_B02_10m')]
    assert isinstance(rectangular_yt_container, YTRegion)
