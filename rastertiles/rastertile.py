from typing import Optional, Any, Dict, Tuple, TYPE_CHECKING
from utils.profile import trace
from exceptions import exception

import contextlib
import numpy as np
import warnings


if TYPE_CHECKING:  # pragma: no cover
    from rasterio.io import DatasetReader  # noqa: F401

def get_resampling_enum(method: str) -> Any:
    from rasterio.enums import Resampling

    if method == "nearest":
        return Resampling.nearest

    if method == "linear":
        return Resampling.bilinear

    if method == "cubic":
        return Resampling.cubic

    if method == "average":
        return Resampling.average

    raise ValueError(f"unknown resampling method {method}")

def has_alpha_band(src: "DatasetReader") -> bool:
    from rasterio.enums import MaskFlags, ColorInterp

    return (
        any([MaskFlags.alpha in flags for flags in src.mask_flag_enums])
        or ColorInterp.alpha in src.colorinterp
    )


@trace("get_raster_tile")
def get_raster_tile(
    path: str,
    *,
    reprojection_method: str = "nearest",
    resampling_method: str = "nearest",
    tile_bounds: Optional[Tuple[float, float, float, float]] = None,
    tile_size: Tuple[int, int] = (256, 256),
    preserve_values: bool = False,
    target_crs: str = "epsg:3857",
    rio_env_options: Optional[Dict[str, Any]] = None,
) -> np.ma.MaskedArray:
    """Load a raster dataset from a file through rasterio.

    Heavily inspired by mapbox/rio-tiler
    """
    import rasterio
    from rasterio import transform, windows, warp
    from rasterio.vrt import WarpedVRT
    from affine import Affine

    dst_bounds: Tuple[float, float, float, float]

    if rio_env_options is None:
        rio_env_options = {}

    if preserve_values:
        reproject_enum = resampling_enum = get_resampling_enum("nearest")
    else:
        reproject_enum = get_resampling_enum(reprojection_method)
        resampling_enum = get_resampling_enum(resampling_method)

    with contextlib.ExitStack() as es:
        es.enter_context(rasterio.Env(**rio_env_options))
        try:
            with trace("open_dataset"):
                src = es.enter_context(rasterio.open(path))
        except OSError:
            raise IOError("error while reading file {}".format(path))

        # compute buonds in target CRS
        dst_bounds = warp.transform_bounds(src.crs, target_crs, *src.bounds)
    
        if tile_bounds is None:
            tile_bounds = dst_bounds

        # prevent loads of very sparse data
        cover_ratio = (
            (dst_bounds[2] - dst_bounds[0])
            / (tile_bounds[2] - tile_bounds[0])
            * (dst_bounds[3] - dst_bounds[1])
            / (tile_bounds[3] - tile_bounds[1])
        )

        if cover_ratio < 0.01:
            raise exception.TileOutOfBoundsError("dataset covers less than 1% of tile")

        # compute suggested resolution in target CRS
        dst_transform, _, _ = warp.calculate_default_transform(
            src.crs, target_crs, src.width, src.height, *src.bounds
        )
        dst_res = (abs(dst_transform.a), abs(dst_transform.e))

        # in some cases (e.g. at extreme latitudes), the default transform
        # suggests very coarse resolutions - in this case, fall back to native tile res
        tile_transform = transform.from_bounds(*tile_bounds, *tile_size)
        tile_res = (abs(tile_transform.a), abs(tile_transform.e))

        if tile_res[0] < dst_res[0] or tile_res[1] < dst_res[1]:
            dst_res = tile_res
            resampling_enum = get_resampling_enum("nearest")

        # pad tile bounds to prevent interpolation artefacts
        num_pad_pixels = 2

        # compute tile VRT shape and transform
        dst_width = max(1, round((tile_bounds[2] - tile_bounds[0]) / dst_res[0]))
        dst_height = max(1, round((tile_bounds[3] - tile_bounds[1]) / dst_res[1]))
        vrt_transform = transform.from_bounds(
            *tile_bounds, width=dst_width, height=dst_height
        ) * Affine.translation(-num_pad_pixels, -num_pad_pixels)
        vrt_height, vrt_width = (
            dst_height + 2 * num_pad_pixels,
            dst_width + 2 * num_pad_pixels,
        )

        # remove padding in output
        out_window = windows.Window(
            col_off=num_pad_pixels,
            row_off=num_pad_pixels,
            width=dst_width,
            height=dst_height,
        )

        # construct VRT
        vrt = es.enter_context(
            WarpedVRT(
                src,
                crs=target_crs,
                resampling=reproject_enum,
                transform=vrt_transform,
                width=vrt_width,
                height=vrt_height,
                add_alpha=not has_alpha_band(src),
            )
        )

        # read data
        with warnings.catch_warnings(), trace("read_from_vrt"):
            warnings.filterwarnings("ignore", message="invalid value encountered.*")
            tile_data = vrt.read(
                1, resampling=resampling_enum, window=out_window, out_shape=tile_size
            )

            # assemble alpha mask
            mask_idx = vrt.count
            mask = vrt.read(mask_idx, window=out_window, out_shape=tile_size) == 0

            if src.nodata is not None:
                mask |= tile_data == src.nodata


    return np.ma.masked_array(tile_data, mask=mask)