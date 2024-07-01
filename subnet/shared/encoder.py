import json
import base64
from enum import Enum


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.name
        return json.JSONEncoder.default(self, obj)


def encode_bytes(obj):
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("utf-8")
    return obj
