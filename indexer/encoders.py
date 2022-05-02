import json
from bson import ObjectId


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def python_to_json(data):
    return JSONEncoder().encode(data)


def pyId(_id: str) -> ObjectId:
    return ObjectId(_id)
