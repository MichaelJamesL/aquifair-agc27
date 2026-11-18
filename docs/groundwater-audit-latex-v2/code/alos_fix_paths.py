"""(Spark) Rewrite the WSL work path inside ISCE shelve files (pickled frames) and XML/VRT headers.
Usage: python alos_fix_paths.py DIR [DIR ...]   e.g. SLC_crop/20080610"""
import glob, os, shelve, sys, types
import isce  # noqa: F401  (registers ISCE modules so the pickled frames load)

OLD, NEW = "/home/user/alos_work", os.path.expanduser("~/alos_work")


def fix(o, seen):
    if isinstance(o, str):
        return o.replace(OLD, NEW)
    if id(o) in seen or isinstance(o, (type, types.ModuleType, types.FunctionType)):
        return o
    seen.add(id(o))
    if isinstance(o, list):
        o[:] = [fix(v, seen) for v in o]
    elif isinstance(o, dict):
        for k in list(o):
            o[k] = fix(o[k], seen)
    elif hasattr(o, "__dict__"):
        for k, v in list(vars(o).items()):
            try:
                setattr(o, k, fix(v, seen))
            except (AttributeError, TypeError):
                pass
    return o


for d in sys.argv[1:]:
    for dat in glob.glob(f"{d}/*.dat"):
        name = dat[:-4]
        with shelve.open(name) as db:
            for k in list(db):
                db[k] = fix(db[k], set())
        with open(dat, "rb") as f:
            assert OLD.encode() not in f.read(), dat
    for h in glob.glob(f"{d}/*.xml") + glob.glob(f"{d}/*.vrt"):
        t = open(h).read()
        if OLD in t:
            open(h, "w").write(t.replace(OLD, NEW))
    print("fixed", d)
