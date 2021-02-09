import numpy as np
import rasterio
from rasterio.windows import Window

from yt.geometry.selection_routines import \
    GridSelector

from yt.frontends.ytdata.io import \
    IOHandlerYTGridHDF5

from .utilities import rasterio_window_calc

class IOHandlerGeoTiff(IOHandlerYTGridHDF5):
    _dataset_type = "geotiff"
    _base = slice(None)
    _field_dtype = "float64"
    _cache_on = False

    def __init__(self, ds, *args, **kwargs):
        super(IOHandlerGeoTiff, self).__init__(ds)

    def _read_fluid_selection(self, chunks, selector, fields, size):
        rv = {}
        chunks = list(chunks)

        if isinstance(selector, GridSelector):
            if not (len(chunks) == len(chunks[0].objs) == 1):
                raise RuntimeError
            g = chunks[0].objs[0]

            if g.id in self._cached_fields:
                gf = self._cached_fields[g.id]
                rv.update(gf)

            if len(rv) == len(fields): return rv
            src = rasterio.open(g.filename, "r")
            for field in fields:
                if field in rv:
                    self._hits += 1
                    continue
                self._misses += 1
                ftype, fname = field

                rv[(ftype, fname)] = src.read(int(fname)).astype(self._field_dtype) # Read in the band/field

            if self._cache_on:
                self._cached_fields.setdefault(g.id,{}) # Reading into cache
                self._cached_fields[g.id].update(rv)
            return rv

        if size is None:
            size = sum((g.count(selector) for chunk in chunks
                        for g in chunk.objs))
        for field in fields:
            ftype, fname = field
            fsize = size
            rv[field] = np.empty(fsize, dtype="float64")
        ind = 0

        for chunk in chunks:
            src = None
            for g in chunk.objs:
                if g.filename is None: continue
                if src is None:
                    src = rasterio.open(g.filename, "r")
                gf = self._cached_fields.get(g.id,{})
                nd = 0

                # Determine the window dimensions of a given selector
                left_edge, right_edge, width, height = rasterio_window_calc(selector)

                # Build Rasterio window-read format
                rasterio_wr_dim = Window(
                    left_edge[0]/src.res[0], left_edge[1]/src.res[1],
                    width/src.res[0], height/src.res[1])

                for field in fields:
                    if field in gf:   # only for cached gridded objects

                        # Add third dimension to numpy array
                        for dim in range(len(gf[field].shape), 3): # change to 3d
                               gf[field] = np.expand_dims(gf[field], dim)

                        nd = g.select(selector, gf[field], rv[field], ind)

                        self._hits += 1
                        continue

                    self._misses += 1

                    ftype, fname = field

                    # Perform Rasterio window read
                    data = src.read(int(fname),window=rasterio_wr_dim).astype(
                        self._field_dtype)

                    for dim in range(len(data.shape), 3): # change to 3d
                        data = np.expand_dims(data, dim)

                    if self._cache_on:
                        self._cached_fields.setdefault(g.id, {})
                        self._cached_fields[g.id][field] = data

                    nd = g.select(selector, data, rv[field], ind)

                ind += nd

        return rv

    def _read_particle_coords(self, chunks, ptf):
        pass

    def _read_particle_fields(self, chunks, ptf, selector):
        pass
