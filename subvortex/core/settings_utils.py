import os
from typing import get_type_hints
from dataclasses import fields, is_dataclass, MISSING


def create_settings_instance(cls, prefix="SUBVORTEX"):
    if not is_dataclass(cls):
        raise TypeError(f"{cls.__name__} must be a dataclass.")

    combined = {}
    type_hints = get_type_hints(cls)

    for field in fields(cls):
        field_type = type_hints.get(field.name, str)
        field_key = f"{prefix}_{field.name.upper()}"

        # ✅ Skip env override if metadata says readonly
        if field.metadata.get("readonly"):
            if field.default is not MISSING:
                combined[field.name] = field.default
            elif field.default_factory is not MISSING:  # type: ignore
                combined[field.name] = field.default_factory()  # type: ignore
            continue

        # 🧠 Handle nested dataclasses
        if is_dataclass(field_type):
            combined[field.name] = create_settings_instance(
                field_type, prefix=field_key
            )
            continue

        # 📦 Handle environment override
        if field_key in os.environ:
            raw_value = os.environ[field_key]
            try:
                if field_type == bool:
                    combined[field.name] = raw_value.lower() in (
                        "1",
                        "true",
                        "yes",
                        "on",
                    )
                else:
                    combined[field.name] = field_type(raw_value)
            except Exception as e:
                raise ValueError(
                    f"Invalid env var {field_key}: cannot cast '{raw_value}' to {field_type.__name__}"
                ) from e
        elif field.default is not MISSING:
            combined[field.name] = field.default
        elif field.default_factory is not MISSING:  # type: ignore
            combined[field.name] = field.default_factory()  # type: ignore

    return cls(**combined)
