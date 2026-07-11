from typing import Any, Dict, List


_JSON_TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "object": dict,
    "array": list,
}


def validate_json_schema(payload: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    errors: List[str] = []
    expected_type = schema.get("type")
    if expected_type:
        py_type = _JSON_TYPE_MAP[expected_type]
        if not isinstance(payload, py_type):
            return [f"{path}: expected type {expected_type}"]

    if expected_type == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in payload:
                errors.append(f"{path}.{key}: missing required property")
        for key, value in payload.items():
            if key in properties:
                errors.extend(validate_json_schema(value, properties[key], f"{path}.{key}"))

    if expected_type == "array":
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(payload):
                errors.extend(validate_json_schema(item, item_schema, f"{path}[{idx}]"))

    if "enum" in schema and payload not in schema["enum"]:
        errors.append(f"{path}: value {payload!r} not in enum")

    if "minimum" in schema and isinstance(payload, (int, float)) and payload < schema["minimum"]:
        errors.append(f"{path}: value {payload} is below minimum {schema['minimum']}")

    if "maximum" in schema and isinstance(payload, (int, float)) and payload > schema["maximum"]:
        errors.append(f"{path}: value {payload} is above maximum {schema['maximum']}")

    if schema.get("minLength") is not None and isinstance(payload, str):
        if len(payload) < schema["minLength"]:
            errors.append(f"{path}: string shorter than minLength={schema['minLength']}")

    return errors
