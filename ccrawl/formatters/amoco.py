# from amoco.system import structs
from ccrawl.utils import c_type, cxx_type
from click import secho
from tinydb import where

__all__ = [
    "cTypedef_amoco",
    "cMacro_amoco",
    "cFunc_amoco",
    "cEnum_amoco",
    "cStruct_amoco",
    "cUnion_amoco",
]

tostruct = {
    "void": "x",
    "_Bool": "?",
    "char": "c",
    "unsigned char": "B",
    "short": "h",
    "unsigned short": "H",
    "int": "i",
    "unsigned int": "I",
    "long": "l",
    "unsigned long": "L",
    "float": "f",
    "ssize_t": "n",
    "size_t": "N",
    "double": "d",
    "long long": "q",
    "unsigned long long": "Q",
}


def id_amoco(s):
    s = s.replace("$","_").replace(":","_")
    return s.replace("?_", "").replace(" ", "_")


def fieldformat(r):
    t = r.lbase
    rt = "P" if r.is_ptr else tostruct.get(t, None)
    if rt is None:
        t = id_amoco(t)
    if r.dim > 0:
        if rt == "x":
            raise TypeError(r)
        if rt in ("c", "B"):
            rt = "s"
        if rt:
            rt = "{} * {:d}".format(rt, r.dim)
        else:
            t = "{} * {:d}".format(t, r.dim)
    elif r.lbfw > 0:
        if rt:
            rt = "{} *#{:d}".format(rt, r.lbfw)
        else:
            t = "{} *#{:d}".format(t, r.lbfw)
    return rt, t


def cTypedef_amoco(obj, db, recursive):
    pre = ""
    t = c_type(obj)
    if isinstance(recursive, set) and (t.lbase not in tostruct):
        recursive.add(obj.identifier)
        Q = db.tag & (where("id") == t.lbase)
        if db.contains(Q):
            x = obj.from_db(db.get(Q))
            pre = x.show(db, recursive, form="amoco")
            pre += "\n\n"
        else:
            secho(f"identifier {t.lbase} not found", fg="red", err=True)
    rn, n = fieldformat(t)
    return f"{pre}TypeDefine('{obj.identifier}','{rn or n}')"


def cMacro_amoco(obj, db, recursive):
    v = obj.strip()
    try:
        v = int(v, base=0)
        return "{} = 0x{:x}".format(obj.identifier, v)
    except ValueError:
        pass
    return f"{obj.identifier} = '{v}'"


def cFunc_amoco(obj, db, recursive):
    pass


def cEnum_amoco(obj, db, recursive):
    n = obj.identifier.replace(" ", "_")
    s = [f"TypeDefine('{n}','i')"]
    s.extend(f"{k} = {v}" for (k, v) in obj.items())
    return "\n".join(s)


def cClass_amoco(obj, db, recursive):
    return cStruct_amoco(obj.as_cStruct(db), db, recursive)

def cStruct_amoco(obj, db, recursive):
    if isinstance(recursive, set):
        if obj.identifier in recursive:
            return ""
        Q = True
        recursive.update(tostruct)
        recursive.add(obj.identifier)
    else:
        Q = None
    name = id_amoco(obj.identifier)
    cls = "UnionDefine" if obj._is_union else "StructDefine"
    R = []
    S = [f'@{cls}("""\n']
    for i in obj:
        t, n, c = i
        r = c_type(t)
        if not n and not r.lbase.startswith("union "):
            continue
        if Q and (r.lbase not in recursive):
            q = db.tag & (where("id") == r.lbase)
            if r.lbase.startswith("?_"):
                q &= where("src") == obj.identifier
            if db.contains(q):
                x = obj.from_db(db.get(q))
                x = x.show(db, recursive, form="amoco")
                x = x.split("\n")
                R.extend(xrl + "\n" for xrl in x if xrl)
                recursive.add(r.lbase)
            else:
                secho(f"identifier {r.lbase} not found", fg="red", err=True)
        rt, t = fieldformat(r)
        if rt:
            t = rt
        if c and c.count("\n") > 0:
            c = None
        S.append(f'{t} : {n} ;{c or ""}\n')
    if R:
        R.append("\n")
    S.extend(
        (
            '""")\nclass %s(StructFormatter):' % name,
            """
    def __init__(self,data="",offset=0):
        if data: self.unpack(data,offset)
    """,
        )
    )
    return "".join(R) + "".join(S)


cUnion_amoco = cStruct_amoco
