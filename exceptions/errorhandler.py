import marshmallow
from flask import Flask ,send_file,jsonify,current_app
from typing import  Callable, Type,Any,TYPE_CHECKING,cast
from exceptions import exception


def _abort(status_code: int, message: str = "") -> Any:
    response = jsonify({"message": message})
    response.status_code = status_code
    return response


def _setup_error_handlers(app: Flask) -> None:
    def register_error_handler(
        exc: Type[Exception], func: Callable[[Exception], Any]
    ) -> None:
        if TYPE_CHECKING:  # pragma: no cover
            # Flask defines this type only during type checking
            from flask.typing import ErrorHandlerCallable

            func = cast(ErrorHandlerCallable, func)

        app.register_error_handler(exc, func)

    def handle_tile_out_of_bounds_error(exc: Exception) -> Any:
        # send empty image
        from settings.setting import get_settings
        from rastertiles.image import empty_image

        settings = get_settings()
        return send_file(
            empty_image(settings.get('DEFAULT_TILE_SIZE')), mimetype="image/png"
        )

    register_error_handler(
        exception.TileOutOfBoundsError, handle_tile_out_of_bounds_error
    )


    def handle_marshmallow_validation_error(exc: Exception) -> Any:
        # wrong query arguments -> 400
        if current_app.debug:
            raise exc
        return _abort(400, str(exc))

    validation_errors = (
        exception.InvalidArgumentsError,
        exception.InvalidKeyError,
        marshmallow.ValidationError,
    )

    for err in validation_errors:
        register_error_handler(err, handle_marshmallow_validation_error)