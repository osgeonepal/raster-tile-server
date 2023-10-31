import os 
from flask import Flask ,send_file, Response, request, jsonify
from flask_cors import CORS
from typing import Optional, Tuple
from schemas.schema import RGBOptionSchema
from dotenv import load_dotenv


flask_app = Flask(__name__)
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv()


#handle Cors
CORS(flask_app, resources={
    r"/tile/*": {"origins": "*"},
    r"/tile-async/*": {"origins": "*"},
})

@flask_app.route('/tile/<path:id>/<int:z>/<int:x>/<int:y>.png')
def get_tile(id , z , x, y):

    from utils.generate_image import generate_image
    optimized_path = os.getenv("OPTIMIZED_PATH")
    tiff_files = [f"{optimized_path}{id}_red.tif", f"{optimized_path}{id}_green.tif", f"{optimized_path}{id}_blue.tif"]

    def generate_image_async(tiff_files, id , z , x, y):
        return generate_image(tiff_files,id , z , x, y)
    
    futures = generate_image_async(tiff_files, id , z , x, y) 
    image = futures
    return send_file(image, mimetype="image/png")


@flask_app.route('/tile-async/<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png')
def get_tile_async(tile_z: int, tile_y: int, tile_x: int, keys: str = "") -> Response:
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

    image = rgb(
        some_keys,
        rgb_values,
        stretch_ranges=stretch_ranges,
        tile_xyz=tile_xyz,
        **options,
    )

    return send_file(image, mimetype="image/png")

@flask_app.route('/bounds/<path:id>')
def get_bounds(id):
    try:
        from utils.createbbox import createbbox
        optimized_path = os.getenv("OPTIMIZED_PATH")
        tiff_file = f"{optimized_path}{id}_red.tif"
        bounds = createbbox(tiff_file)
        if bounds:
            return jsonify({"bounds":bounds})
    except:
        return jsonify({"message":"File not found"})
    
    

