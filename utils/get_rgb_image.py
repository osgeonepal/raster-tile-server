from typing import Optional, Tuple
from schemas.schema import RGBOptionSchema
from flask import send_file, Response, request



def _get_rgb_image(
    keys: str, tile_xyz: Optional[Tuple[int, int, int]] = None
) -> Response:
    from rastertiles.rgb import rgb

    option_schema = RGBOptionSchema()
    options = option_schema.load(request.args)

    some_keys = [key for key in keys.split("/") if key]

    rgb_values = (options.pop("r"), options.pop("g"), options.pop("b"))
    stretch_ranges = tuple(options.pop(k) for k in ("r_range", "g_range", "b_range"))

    image = rgb(
        some_keys,
        rgb_values,
        stretch_ranges=stretch_ranges,
        tile_xyz=tile_xyz,
        **options,
    )

    return send_file(image, mimetype="image/png")