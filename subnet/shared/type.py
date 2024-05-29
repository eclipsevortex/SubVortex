def get_key_from_value(value, enum):
    for key, val in enum.items():
        if val == value:
            return key
    return None


def get_enum_name_from_value(value, enum):
    for rule in enum:
        if rule.key == value:
            return rule.name
    return None


def get_enum_name_from_value(name, enum):
    try:
        return enum[name]
    except KeyError:
        return None