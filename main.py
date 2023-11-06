import os
import copy
from flask import Flask, Response, jsonify, Blueprint, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from exceptions import errorhandler
from flasgger import Swagger
from flasgger import swag_from


load_dotenv()
flask_app = Flask(__name__)
flask_app.config["JSON_SORT_KEYS"] = False
base_dir = os.path.dirname(os.path.abspath(__file__))
TILE_API = Blueprint("tile_api", __name__)
errorhandler._setup_error_handlers(flask_app)

swagger = Swagger(flask_app)


# handle Cors
CORS(flask_app, resources={
    r"/tile-async/*": {"origins": "*"},
    r"/bounds/*": {"origins": "*"},
})


@flask_app.route('/')
def upload():
    return render_template("upload.html")


@TILE_API.route('/tile-async/<path:keys>/<int:tile_z>/<int:tile_x>/<int:tile_y>.png')
@swag_from('docs/get_tile_async.yml')
def get_tile_async(tile_z: int, tile_y: int, tile_x: int, keys: str = "") -> Response:
    tile_xyz = (tile_x, tile_y, tile_z)
    from utils.get_rgb_image import _get_rgb_image
    return _get_rgb_image(keys, tile_xyz=tile_xyz)


@TILE_API.route('/bounds/<path:id>', methods=["GET"])
@swag_from('docs/get_bounds.yml')
def get_bounds(id):
    try:
        from utils.createbbox import createbbox
        optimized_path = os.getenv("OPTIMIZED_PATH")
        tiff_file = f"{optimized_path}{id}_red.tif"
        bounds = createbbox(tiff_file)
        if bounds:
            return jsonify({"bounds": bounds})
    except:
        return jsonify({"message": "File not found"})


# extensions might modify the global blueprints, so copy before use
new_tile_api = copy.deepcopy(TILE_API)
flask_app.register_blueprint(new_tile_api, url_prefix="/")
