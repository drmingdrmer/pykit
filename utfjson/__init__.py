import sys

from .utfjson import (
    dump,
    load,
)

_pyver = sys.version_info.major

if _pyver == 2:
    from pykit.p3json import (
        JSONDecodeError,
    )
else:
    from json import JSONDecodeError

__all__ = [
    'dump',
    'load',
    "JSONDecodeError",
]
