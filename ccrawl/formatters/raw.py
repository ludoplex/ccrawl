import pprint

__all__ = ["ccore_raw"]

# default raw formatter:
# ------------------------------------------------------------------------------


def ccore_raw(obj, db, recursive):
    return f"{obj.identifier}:\n{pprint.pformat(obj)}"


default = ccore_raw
