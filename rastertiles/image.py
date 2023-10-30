"""image.py

Utilities to create and manipulate images.
"""

from typing import Sequence, Tuple, TypeVar, Union
from typing.io import BinaryIO

from io import BytesIO

import numpy as np
from PIL import Image

from utils.profile import trace
from settings.setting import get_settings

Number = TypeVar("Number", int, float)
RGBA = Tuple[Number, Number, Number, Number]
Palette = Sequence[RGBA]
Array = Union[np.ndarray, np.ma.MaskedArray]


@trace("array_to_png")
def array_to_png(
    img_data: Array, colormap: Union[str, Palette, None] = None
) -> BinaryIO:
    """Encode an 8bit array as PNG"""
    transparency: Union[Tuple[int, int, int], int, bytes]

    settings = get_settings()
    compress_level = settings.get('PNG_COMPRESS_LEVEL')

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
            
   

@trace("contrast_stretch")
def contrast_stretch(
    data: Array,
    in_range: Sequence[Number],
    out_range: Sequence[Number],
    clip: bool = True,
) -> Array:
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


def to_uint8(data: Array, lower_bound: Number, upper_bound: Number) -> Array:
    """Re-scale an array to [1, 255] and cast to uint8 (0 is used for transparency)"""
    rescaled = contrast_stretch(data, (lower_bound, upper_bound), (1, 255), clip=True)
    rescaled = np.rint(rescaled)
    return rescaled.astype(np.uint8)

