"""
Utility functions for yt_geotiff.



"""
import numpy as np
import rasterio
from rasterio.windows import Window
from unyt import unyt_array, uconcatenate

# AR
import pdb # debugging library
import yt.geometry.selection_routines as selector_shape

def coord_cal(xcell, ycell, transform):
    """Function to calculate the position of cell (xcell, ycell) in terms of
    longitude and latitude"""


    # note dy is -ve
    dx, rotx, xmin, roty, dy, ymax = transform[0:6]
    xp = xmin + dx/2 + dx*xcell + rotx*ycell
    yp = ymax + dy/2 + dy*ycell + roty*xcell

    return xp, yp

def left_aligned_coord_cal(xcell, ycell, transform):
    """Function to calculate the position of cell (xcell, ycell) in terms of
    distance from the top left corner using the longitude and latitude of
    the cell and the Earth radius to calculate an arc distance.
    This is required for yt as it needs to work with the distances rather than
    degrees.
    """

    # rEarth = 6.371e6 # metres

    dx, rotx, xmin, roty, dy, ymax = transform[0:6]
    xp, yp = coord_cal(xcell, ycell, transform)
    # convert to meters
    x_arc_dist = (xp - xmin)# * np.pi/180. * rEarth
    y_arc_dist = (ymax - yp)# * np.pi/180. * rEarth # (0, 0) corresponds to (xmin, ymax)
    return x_arc_dist, y_arc_dist

def parse_awslandsat_metafile(filename, flatdict=True):
    """Function to read in metadata/parameter file and output it as a dict.
    """

    f = open(filename, 'r') 
    groupkeys = []

    data = {}

    while True: 

        # Get next line from file
        line = f.readline().strip().replace('"', '').replace('\n', '')

        # if line is empty 
        # end of file is reached 
        if not line or line == 'END': 
            break
        key, value = line.split(' = ')

        # make sure we have all of value if it is an array
        while value.count('(') != value.count(')'):
            line = f.readline().strip().replace('"', '').replace('\n', '')
            value += line

        # save to data dictionary
        if key == 'GROUP':
            groupkeys.append(value)
        elif key == 'END_GROUP':
            groupkeys.pop()
        else:
            if flatdict: # save as flat dictionary?
                data[key] = value
            else: # useful if keys are not unique for each band
                data[tuple(groupkeys + [key])] = value

    f.close() 

    return data

def save_dataset_as_geotiff(ds, filename):
    r"""Export georeferenced dataset to a reloadable geotiff.

    This function is a wrapper for rasterio's geotiff writing capability. The
    dataset used must be of the geotiff class (or made to be similar). The 
    transform and other metadata are then taken from the dataset parameters.
    This resulting file is a multi- (or single-) band geotiff which can then be
    loaded by yt or other packages.

    Parameters
    ----------
    ds : dataset
        The georeferenced dataset to be saved to file.
    filename: str
        The name of the file to be written.

    Returns
    -------
    filename : str
        The name of the file that has been created.
    """
    # create a 3d numpy array which is structured as (bands, rows, columns)
    # cycle through each field(/band).
    count = ds.parameters['count']
    bands = range(1, count + 1)
    output_array = np.array([np.array(ds.index.grids[0][('bands', str(b))])[:,:,0] for b in bands])
    dtype = output_array[0].dtype

    with rasterio.open(filename,
                       'w',
                       driver='GTiff',
                       height=ds.parameters['height'],
                       width=ds.parameters['width'],
                       count=count,
                       dtype=dtype,
                       crs=ds.parameters['crs'],
                       transform=ds.parameters['transform'],
                      ) as dst:
        dst.write(output_array)

    return filename

def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result
      

def rasterio_window_calc(selector):
       """ 
       This function reads information from either a sphere, box or region selector 
       object and outputs the dimensions of a container: left edge, right edge,
       width and height.
       
       Output uses:
              - Construct dimensions to perform a Rasterio Window Read
              - Provide a temporary update ro the image domain size             
       """        
       #pdb.set_trace()
       if type(selector) == selector_shape.SphereSelector:
              print('Sphere selector')
              
              selector_left_edge = [(selector.center[0] - selector.radius),(selector.center[1] - selector.radius), selector.center[2]]
              selector_right_edge = [(selector.center[0] + selector.radius),(selector.center[1] + selector.radius), selector.center[2]] 
              
              selector_width = ((selector.radius)*2)
              
              selector_height = selector_width
                                    
       elif type(selector) == selector_shape.RegionSelector:
              print('Box or region selector')
              
              selector_left_edge = selector.left_edge
              selector_right_edge = selector.right_edge
              
              selector_width =  selector.right_edge[0] - selector.left_edge[0]
              
              selector_height = selector_width
                 
       return(np.array(selector_left_edge), np.array(selector_right_edge), selector_width, selector_height)

def validate_coord_array(ds, coord, name, padval, def_units):
    """
    Take a length 2 or 3 array and return a length 3 array.
    If array is length 2, use padval for third value.
    """
    if not isinstance(coord, np.ndarray):
        raise ValueError(
            f"{name} argument must be array-like: {coord}.")

    if coord.size == 3:
        return coord
    if coord.size != 2:
        raise ValueError(
            f"{name} argument must be of size 2 or 3.")

    if isinstance(coord, unyt_array):
        cfunc = uconcatenate
        afunc = ds.arr
        units = coord.units
        padval = ds.arr([padval])
    elif isinstance(coord, np.ndarray):
        cfunc = np.concatenate
        afunc = np.array
        units = "code_length"

    newc = cfunc([coord, afunc(padval.to(units))])
    return newc
