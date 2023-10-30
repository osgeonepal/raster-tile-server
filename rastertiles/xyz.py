"""xyz.py

Utilities to work with XYZ Mercator tiles.
"""

from typing import Optional, Sequence, Union, Mapping, Tuple, Any
import mercantile
from exceptions import exception
from drivers.terracotta_driver import DataDriver

# TODO: add accurate signature if mypy ever supports conditional return types
def get_tile_data(
    driver: DataDriver,
    keys: Union[Sequence[str], Mapping[str, str]],
    tile_xyz: Optional[Tuple[int, int, int]] = None,
    *,
    tile_size: Tuple[int, int] = (256, 256),
    preserve_values: bool = False,
    asynchronous: bool = False,
) -> Any:
    """Retrieve raster image from key_names for given XYZ tile and keys"""
    if tile_xyz is None:
        # read whole dataset
        return driver.get_raster_tile(
            keys,
            tile_size=tile_size,
            preserve_values=preserve_values,
            asynchronous=asynchronous,
        )

    # determine bounds for given tile
    # metadata = key_names.get_metadata(keys)
    # wgs_bounds = metadata["bounds"]
    # wgs_bounds=transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
    wgs_bounds=(-107.88857386093643, 38.98669825130578, -107.8871274949119, 38.98772137392041)

    tile_x, tile_y, tile_z = tile_xyz

    # if not tile_exists(wgs_bounds, tile_x, tile_y, tile_z):
    #     raise exception.TileOutOfBoundsError(
    #         f"Tile {tile_z}/{tile_x}/{tile_y} is outside image bounds"
    #     )

    mercator_tile = mercantile.Tile(x=tile_x, y=tile_y, z=tile_z)
    target_bounds = mercantile.xy_bounds(mercator_tile)

    return driver.get_raster_tile(
        keys,
        tile_bounds=target_bounds,
        tile_size=tile_size,
        preserve_values=preserve_values,
        asynchronous=asynchronous,
    )


def tile_exists(bounds: Sequence[float], tile_x: int, tile_y: int, tile_z: int) -> bool:
    """Check if an XYZ tile is inside the given physical bounds."""
    mintile = mercantile.tile(bounds[0], bounds[3], tile_z)
    maxtile = mercantile.tile(bounds[2], bounds[1], tile_z)

    return mintile.x <= tile_x <= maxtile.x and mintile.y <= tile_y <= maxtile.y
