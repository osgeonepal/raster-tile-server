from marshmallow import Schema, fields, validate, pre_load, ValidationError, EXCLUDE
from typing import  Any, Mapping, Dict
import json



class RGBOptionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    r = fields.String(required=True, description="Key value for red band")
    g = fields.String(required=True, description="Key value for green band")
    b = fields.String(required=True, description="Key value for blue band")
    r_range = fields.List(
        fields.Number(allow_none=True),
        validate=validate.Length(equal=2),
        example="[0,1]",
        missing=None,
        description="Stretch range [min, max] to use for red band as JSON array",
    )
    g_range = fields.List(
        fields.Number(allow_none=True),
        validate=validate.Length(equal=2),
        example="[0,1]",
        missing=None,
        description="Stretch range [min, max] to use for green band as JSON array",
    )
    b_range = fields.List(
        fields.Number(allow_none=True),
        validate=validate.Length(equal=2),
        example="[0,1]",
        missing=None,
        description="Stretch range [min, max] to use for blue band as JSON array",
    )
    tile_size = fields.List(
        fields.Integer(),
        validate=validate.Length(equal=2),
        example="[256,256]",
        description="Pixel dimensions of the returned PNG image as JSON list.",
    )

    @pre_load
    def process_ranges(self, data: Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]:
        data = dict(data.items())
        for var in ("r_range", "g_range", "b_range", "tile_size"):
            val = data.get(var)
            if val:
                try:
                    data[var] = json.loads(val)
                except json.decoder.JSONDecodeError as exc:
                    raise ValidationError(
                        f"Could not decode value for {var} as JSON"
                    ) from exc
        return data