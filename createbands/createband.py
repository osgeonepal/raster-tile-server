import os
import math
import rasterio
import tempfile
from rasterio.enums import Resampling
from rasterio.io import  MemoryFile
from rasterio.shutil import copy


file_path = "/Users/anupdahal/outsource/decoding/flask-tile-api/raw/Alabu_Afd76_Fortunavej1646_okt2023.tif"  # Replace with the path to your input multi-band GeoTIFF
output_folder = "/Users/anupdahal/outsource/decoding/flask-tile-api/optimized" 
nodata_value = 0
GDAL_CONFIG={'GDAL_TIFF_INTERNAL_MASK': True, 'GDAL_TIFF_OVR_BLOCKSIZE': 256, 'GDAL_CACHEMAX': 536870912, 'GDAL_SWATH_SIZE': 1073741824}
COG_PROFILE = {
    "count": 1,
    "driver": "GTiff",
    "interleave": "pixel",
    "tiled": True,
    "blockxsize": 256,
    "blockysize": 256,
    "photometric": "MINISBLACK",
    'nodata': 0.0,
    "ZLEVEL": 1,
    "ZSTD_LEVEL": 9,
    "BIGTIFF": "IF_SAFER",
}
IN_MEMORY_THRESHOLD = 10980 * 10980
RESAMPLING_METHODS = {
                            "average": Resampling.average,
                            "nearest": Resampling.nearest,
                            "bilinear": Resampling.bilinear,
                            "cubic": Resampling.cubic,
                        }

def named_tempfile(basedir):
    print(basedir,'basedir')
    fileobj = tempfile.NamedTemporaryFile(dir=str(basedir), suffix=".tif")
    fileobj.close()
    try:
        yield fileobj.name
    finally:
        os.remove(fileobj.name)



def handleCreateBandsNormal(file_path , id):
    try:
        print(f"*******Create Bands from single Tif ********")
        with rasterio.Env(**GDAL_CONFIG):
            with rasterio.open(file_path) as src:
                for band_number, color in [(1, "red"), (2, "green"), (3, "blue")]:
                    target_crs="epsg:3857"
                    resampling_method = "average"
                    compression = "ZSTD"
                    nproc = 1
                    reproject= False
                    in_memory= None
                    rs_method = RESAMPLING_METHODS[resampling_method]
                    if nproc == -1:
                        nproc = os.cpu_count() or 1  # Default to 1 if `cpu_count` returns None
                    output_file = f"{output_folder}/{id}_{color}.tif"  # Adjust the naming as needed

                    profile = src.profile.copy()
                    profile.update(COG_PROFILE)

                    if in_memory is None:
                        in_memory = src.width * src.height < IN_MEMORY_THRESHOLD

                    if in_memory:
                        print("in memory")
                        memfile = MemoryFile()
                        dst = memfile.open(**profile)
                    else:
                        print("in temporary file")
                        fileobj = tempfile.NamedTemporaryFile(dir=str(output_folder), suffix=".tif")
                        fileobj.close()
                        tempraster=fileobj.name
                        print(tempraster)
                        dst = rasterio.open(tempraster, "w", **profile)
                        

                    if reproject:
                        pass
                    else:
                        pass

                    windows = list(dst.block_windows(1))  
                    print('in middle')           
                    
                    for _, w in windows:
                        block_data = src.read(window=w, indexes=[band_number])
                        dst.write(block_data, window=w)
                        block_mask = src.dataset_mask(window=w).astype("uint8")
                        dst.write_mask(block_mask, window=w)

                    print('in later middle')           
                    

                    # add overviews
                    if not in_memory:
                        # work around bug mapbox/rasterio#1497
                        dst.close()
                        dst = rasterio.open(tempraster, "r+")
                        pass
               

                    max_overview_level = math.ceil(
                        math.log2(
                            max(
                                dst.height // profile["blockysize"],
                                dst.width // profile["blockxsize"],
                                1,
                            )
                        )
                    )



                    if max_overview_level > 0:
                        overviews = [2**j for j in range(1, max_overview_level + 1)]
                        dst.build_overviews(overviews, rs_method)
                        dst.update_tags(ns="rio_overview", resampling=rs_method.value)


                    # copy to destination (this is necessary to push overviews to start of file)
                    copy(dst,str(output_file),copy_src_overviews=True,compress=compression,**COG_PROFILE,) 
                    print('in last middle')   

                    if not in_memory:
                        os.remove(tempraster)
                        pass     

                    print('in end')           


                    
        print(f"*******Completed ********")
        return True

    except Exception as e:
        return str(e)

handleCreateBandsNormal(file_path,"testverybig")