import rasterio
import mercantile
from rasterio.warp import transform_bounds ,calculate_default_transform
from rasterio import transform , windows
from rasterio.vrt import WarpedVRT
from affine import Affine
from rasterio.enums import Resampling , MaskFlags, ColorInterp
import numpy as np
from PIL import Image
from io import BytesIO



class TileOutOfBoundsError(Exception):
    pass

class InvalidArgumentsError(Exception):
    pass

def tile_exists(bounds, x, y,z):
    """Check if an XYZ tile is inside the given physical bounds."""
    mintile = mercantile.tile(bounds[0], bounds[3], z)
    maxtile = mercantile.tile(bounds[2], bounds[1], z)

    return mintile.x <= x <= maxtile.x and mintile.y <= y <= maxtile.y


def has_alpha_band(src):
    return (
        any([MaskFlags.alpha in flags for flags in src.mask_flag_enums])
        or ColorInterp.alpha in src.colorinterp
    )


def get_resampling_enum(method):
    if method == "nearest":
        return Resampling.nearest

    if method == "linear":
        return Resampling.bilinear

    if method == "cubic":
        return Resampling.cubic

    if method == "average":
        return Resampling.average

    raise ValueError(f"unknown resampling method {method}")


def contrast_stretch(data,in_range,out_range,clip= True):
    """Normalize input array from in_range to out_range"""
    lower_bound_in, upper_bound_in = in_range
    lower_bound_out, upper_bound_out = out_range

    out_data = data.astype("float64", copy=True)
    out_data -= lower_bound_in
    norm = upper_bound_in - lower_bound_in
    if abs(norm) > 1e-8:  # prevent division by 0
        out_data *= (upper_bound_out - lower_bound_out) / norm
    out_data += lower_bound_out

    if clip:
        np.clip(out_data, lower_bound_out, upper_bound_out, out=out_data)

    return out_data


def to_uint8(data, lower_bound, upper_bound):
    """Re-scale an array to [1, 255] and cast to uint8 (0 is used for transparency)"""
    rescaled = contrast_stretch(data, (lower_bound, upper_bound), (1, 255), clip=True)
    rescaled = np.rint(rescaled)
    return rescaled.astype(np.uint8)


def array_to_png(img_data, colormap= None) :
    """Encode an 8bit array as PNG"""
    PNG_COMPRESS_LEVEL = 1
    compress_level = PNG_COMPRESS_LEVEL

    if img_data.ndim == 3:  # encode RGB image
        if img_data.shape[-1] != 3:
            raise ValueError("3D input arrays must have three bands")

        if colormap is not None:
            raise ValueError("Colormap argument cannot be given for multi-band data")

        mode = "RGB"
        transparency = (0, 0, 0)
        palette = None      
    else:
        raise ValueError("Input array must have 3 dimensions")

    if isinstance(img_data, np.ma.MaskedArray):
        img_data = img_data.filled(0)

    img = Image.fromarray(img_data, mode=mode)

    if palette is not None:
        img.putpalette(palette)

    sio = BytesIO()
    img.save(sio, "png", compress_level=compress_level, transparency=transparency)
    sio.seek(0)
    return sio


def generate_image(tiff_files,id , z , x, y ):
    target_crs= 'EPSG:3857'
    reprojection_method = "nearest"
    resampling_method = "nearest"
    tile_size= (512, 512)
    mercator_tile = mercantile.Tile(x=x, y=y, z=z)
    target_bounds = mercantile.xy_bounds(mercator_tile)
    reproject_enum = get_resampling_enum(reprojection_method)
    resampling_enum = get_resampling_enum(resampling_method)
    # pad tile bounds to prevent interpolation artefacts
    num_pad_pixels = 2

    out_arrays=[]
    for band in tiff_files:
        with rasterio.open(band) as src:      
            bounds4326 = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
            bounds3857 = transform_bounds(src.crs, target_crs, *src.bounds)
            # compute suggested resolution in target CRS
            default_transform, _, _ = calculate_default_transform(src.crs, target_crs, src.width, src.height, *src.bounds)
            default_resolution = (abs(default_transform.a), abs(default_transform.e))

            if not tile_exists(bounds4326, x, y, z):
                raise TileOutOfBoundsError(
                    f"Tile {z}/{x}/{y} is outside image bounds"
                )
            # prevent loads of very sparse data
            cover_ratio = (
                (bounds3857[2] - bounds3857[0])
                / (target_bounds[2] - target_bounds[0])
                * (bounds3857[3] - bounds3857[1])
                / (target_bounds[3] - target_bounds[1])
            )
            if cover_ratio < 0.01:
                raise TileOutOfBoundsError("dataset covers less than 1% of tile")
            
            # in some cases (e.g. at extreme latitudes), the default transform
            # suggests very coarse resolutions - in this case, fall back to native tile res
            tile_transform = transform.from_bounds(*target_bounds, *tile_size)
            tile_resolution = (abs(tile_transform.a), abs(tile_transform.e))
            if tile_resolution[0] < default_resolution[0] or tile_resolution[1] < default_resolution[1]:
                default_resolution = tile_resolution
                resampling_enum = get_resampling_enum("nearest")

            # compute tile VRT shape and transform
            dst_width = max(1, round((target_bounds[2] - target_bounds[0]) / default_resolution[0]))
            dst_height = max(1, round((target_bounds[3] - target_bounds[1]) / default_resolution[1]))
            vrt_transform = transform.from_bounds(*target_bounds, width=dst_width, height=dst_height) * Affine.translation(-num_pad_pixels, -num_pad_pixels)
            vrt_height, vrt_width = (dst_height + 2 * num_pad_pixels,dst_width + 2 * num_pad_pixels,)


            # remove padding in output
            out_window = windows.Window(
                col_off=num_pad_pixels,
                row_off=num_pad_pixels,
                width=dst_width,
                height=dst_height,
            )

            # construct VRT
            vrt =WarpedVRT(
                    src,
                    crs=target_crs,
                    resampling=reproject_enum,
                    transform=vrt_transform,
                    width=vrt_width,
                    height=vrt_height,
                    add_alpha=not has_alpha_band(src),
                )
            
            tile_data = vrt.read(1, resampling=resampling_enum, window=out_window, out_shape=tile_size)

            # assemble alpha mask
            mask_idx = vrt.count
            mask = vrt.read(mask_idx, window=out_window, out_shape=tile_size) == 0

            if src.nodata is not None:
                mask |= tile_data == src.nodata

            final_array =np.ma.masked_array(tile_data, mask=mask)

            stretch_range_ = [0,255]

            array = to_uint8(final_array, *stretch_range_)

            out_arrays.append(array)


    out = np.ma.stack(out_arrays, axis=-1)
    image=array_to_png(out)
    return image