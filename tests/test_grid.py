import glob
from numpy.testing import assert_almost_equal, assert_equal
import os
import yt
import yt.extensions.geotiff

from yt.config import ytcfg

from yt_geotiff.testing import requires_file

test_data_dir = ytcfg.get("yt", "test_data_dir")
landsat = "Landsat-8_sample_L2/LC08_L2SP_171060_20210227_20210304_02_T1_SR_B1.TIF"
s2 = "M2_Sentinel-2_test_data/T36MVE_20210315T075701_B01.jp2"

landsat_fns = glob.glob(os.path.join(test_data_dir, os.path.dirname(landsat), "*.TIF"))
s2_fns = glob.glob(os.path.join(test_data_dir, os.path.dirname(s2), "*.jp2"))

@requires_file(landsat)
@requires_file(s2)
def test_grid():
    fns = s2_fns + landsat_fns
    ds = yt.load(*fns)

    n1 = ds.data[('bands', 'LS_B1')].shape
    n2 = ds.data[('bands', 'S2_B01')].shape
    assert_equal(n1, n2)
    assert_equal(n1, tuple(ds.data.ActiveDimensions))
