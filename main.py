from flask import Flask ,send_file, Response, request
from flask_cors import CORS
from typing import Optional, Tuple
from schemas.schema import RGBOptionSchema


flask_app = Flask(__name__)



#handle CORS
CORS(flask_app, resources={
    r"/tile/*": {"origins": "http://localhost:5173"},
    r"/tile-new/*": {"origins": "http://localhost:5173"},

})

@flask_app.route('/tile/<path:id>/<int:z>/<int:x>/<int:y>.png')
def get_tile(id , z , x, y):

    from utils.generate_image import generate_image

    tiff_files = ["optimized/testverybig_red.tif", "optimized/testverybig_green.tif","optimized/testverybig_blue.tif"]


    def generate_image_async(tiff_files, id , z , x, y):
        return generate_image(tiff_files,id , z , x, y)
    
    futures = generate_image_async(tiff_files, id , z , x, y) 
    image = futures
    return send_file(image, mimetype="image/png")


@flask_app.route('/tile-new/<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png')
def get_rgb(tile_z: int, tile_y: int, tile_x: int, keys: str = "") -> Response:
    tile_xyz = (tile_x, tile_y, tile_z)
    return _get_rgb_image(keys, tile_xyz=tile_xyz)

def _get_rgb_image(
    keys: str, tile_xyz: Optional[Tuple[int, int, int]] = None
) -> Response:
    from rastertiles.rgb import rgb

    option_schema = RGBOptionSchema()
    options = option_schema.load(request.args)

    some_keys = [key for key in keys.split("/") if key]

    rgb_values = (options.pop("r"), options.pop("g"), options.pop("b"))
    stretch_ranges = tuple(options.pop(k) for k in ("r_range", "g_range", "b_range"))

    # print(some_keys, rgb_values,stretch_ranges,tile_xyz,options)

    image = rgb(
        some_keys,
        rgb_values,
        stretch_ranges=stretch_ranges,
        tile_xyz=tile_xyz,
        **options,
    )

    return send_file(image, mimetype="image/png")
    
    

