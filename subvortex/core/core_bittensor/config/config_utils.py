import os
import argparse
from argparse import Namespace
from dataclasses import is_dataclass, fields

import bittensor.core.config as btcc


def update_config(settings, config: btcc.Config, parser, prefix="SUBVORTEX"):
    if not is_dataclass(settings):
        raise TypeError("settings must be a dataclass instance")

    flat_settings = _flatten_settings(settings)
    updated_keys = set()

    # Apply settings first
    for full_key, value in flat_settings.items():
        parts = full_key.split(".")
        if _has_attr_chain(config, parts):
            _set_real_config_attr(config, parts, value)
            updated_keys.add(".".join(parts))

    # Fallback to env
    for full_key in _gather_config_keys(config):
        if full_key in updated_keys:
            continue

        parts = full_key.split(".")
        env_key = f"{prefix}_{'_'.join(part.upper() for part in parts)}"
        if env_key in os.environ:
            raw_value = os.environ[env_key]
            value = _infer_type_from_parser_or_config(config, parser, parts, raw_value)
            if _has_attr_chain(config, parts):
                _set_real_config_attr(config, parts, value)


def _flatten_settings(settings, prefix=""):
    flat = {}
    for field in fields(settings):
        val = getattr(settings, field.name)
        full_key = f"{prefix}.{field.name}" if prefix else field.name
        if is_dataclass(val):
            flat.update(_flatten_settings(val, full_key))
        else:
            flat[full_key] = val
    return flat


def _set_real_config_attr(config, parts, value):
    current = config
    args = getattr(config, "args", None)  # support for config.args.<nested>

    for part in parts[:-1]:
        if not hasattr(current, part):
            return
        current = getattr(current, part)
        if args and hasattr(args, part):
            args = getattr(args, part)

    final_attr = parts[-1]
    if hasattr(current, final_attr):
        setattr(current, final_attr, value)
    if args and hasattr(args, final_attr):
        setattr(args, final_attr, value)


def _infer_type_from_parser_or_config(config, parser, parts, raw_value):
    # Try from parser
    arg_name = ".".join(parts)
    arg_type = _get_arg_type_from_parser(parser, arg_name)
    if arg_type:
        try:
            if arg_type is bool:
                return raw_value.lower() in ("1", "true", "yes", "on")
            return arg_type(raw_value)
        except Exception:
            pass

    # Fallback to config
    current = config
    for part in parts[:-1]:
        current = getattr(current, part, None)
        if current is None:
            return raw_value

    field = getattr(current, parts[-1], None)
    if field is None:
        return raw_value

    try:
        if isinstance(field, bool):
            return raw_value.lower() in ("1", "true", "yes", "on")
        return type(field)(raw_value)
    except Exception:
        return raw_value


def _gather_config_keys(config, prefix=""):
    keys = []
    if hasattr(config, "to_dict"):
        source = config.to_dict()
    elif isinstance(config, Namespace):
        source = vars(config)
    elif isinstance(config, dict):
        source = config
    else:
        return keys

    for key, val in source.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(val, (dict, Namespace)):
            keys.extend(_gather_config_keys(val, full_key))
        else:
            keys.append(full_key)

    return keys


def _get_arg_type_from_parser(parser: argparse.ArgumentParser, arg_name: str):
    for action in parser._actions:
        if "--" + arg_name in action.option_strings:
            return action.type or (
                bool if action.nargs == 0 and action.const is not None else str
            )
    return None


def _has_attr_chain(config, parts):
    current = config
    for part in parts:
        if isinstance(current, btcc.Config) and part not in current.toDict():
            return False
        if not hasattr(current, part):
            return False
        current = getattr(current, part)
    return True
