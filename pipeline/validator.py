def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)

def validate_output(data):
    if not isinstance(data, dict):
        raise ValueError("Model output must be a JSON object.")

    programs = data.get("programs")
    if not isinstance(programs, list):
        raise ValueError("Model output must contain a 'programs' array.")

    allowed = {
        "type", "name", "year", "description", "beneficiaries_count",
        "budget", "beneficiary_value", "target_audience",
        "delivery_method", "notes"
    }

    cleaned = []
    for i, item in enumerate(programs):
        if not isinstance(item, dict):
            raise ValueError(f"programs[{i}] must be an object.")

        item = {k: item.get(k) for k in allowed}

        if not isinstance(item.get("name"), str) or not item["name"].strip():
            raise ValueError(f"programs[{i}].name must be a non-empty string.")

        if item["year"] is not None and not _number(item["year"]):
            raise ValueError(f"programs[{i}].year must be a number or null.")

        if item["beneficiaries_count"] is not None and not _number(item["beneficiaries_count"]):
            raise ValueError(f"programs[{i}].beneficiaries_count must be a number or null.")

        item["type"] = item.get("type") or "program"
        cleaned.append(item)

    return {"programs": cleaned}
