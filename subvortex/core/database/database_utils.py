# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
from typing import Optional


def decode_value(val: bytes | None) -> Optional[str]:
    return val.decode() if val is not None else None


def decode_hash(raw: dict[bytes, bytes]) -> dict[str, str]:
    return {k.decode(): v.decode() for k, v in raw.items()}


def decode_list(raw: list[bytes]) -> list[str]:
    return [item.decode() for item in raw]


def decode_stream(raw) -> list[dict[str, str]]:
    decoded = []
    for _, messages in raw:
        for _, fields in messages:
            decoded.append({k.decode(): v.decode() for k, v in fields.items()})
    return decoded
