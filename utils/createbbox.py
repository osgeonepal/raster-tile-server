import rasterio
from rasterio.warp import transform_bounds 


def createbbox(band):
    with rasterio.open(band) as src:      
        bounds4326 = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
        src.close()
        return bounds4326

    