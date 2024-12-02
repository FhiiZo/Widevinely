import json
import pathlib

from widevinely.utils import logger

log = logger.getLogger("globals")


class obj:
    def __init__(self, dict):
        self.__dict__.update(dict)


def dict2obj(dict):
    paths = []
    if dict:
        for x in dict:
            if type(dict[x]) in [pathlib.PosixPath, pathlib.WindowsPath]:
                paths.append(x)
                dict[x] = str(dict[x])
        object = json.loads(json.dumps(dict), object_hook=obj)
        if paths:
            for y in paths:
                setattr(object, y, pathlib.Path(dict[y]))
        return object


class arguments:
    def __init__(self, **kwargs):
        self.get(**kwargs)
        self.globalize()

    def get(
        self,
        main=None,
        dl=None,
        cfg=None,
        wvd=None,
        update_=None,
        service=None,
        reset=False,
    ):
        if not globals().get("args") or reset:
            global args
            args = self

        if main:
            args.main = dict2obj(main) if type(main) != obj else main
        if dl:
            args.dl = dict2obj(dl)
        if cfg:
            args.cfg = dict2obj(cfg)
        if wvd:
            args.wvd = dict2obj(wvd)
        if update_:
            args.update_ = dict2obj(update_)
        if service:
            args.service = dict2obj(service)

    def globalize(self):
        if getattr(args, "main", None):
            self.main = args.main
        if getattr(args, "dl", None):
            self.dl = args.dl
        if getattr(args, "cfg", None):
            self.cfg = args.cfg
        if getattr(args, "wvd", None):
            self.wvd = args.wvd
        if getattr(args, "update_", None):
            self.update_ = args.update_
        if getattr(args, "service", None):
            self.service = args.service

        return self


class cdm:
    def __init__(self, **kwargs) -> None:
        self.get(**kwargs)
        self.globalize()

    def get(self, cdm_device=None, reset=False):
        if not globals().get("cdm_") or reset:
            global cdm_
            cdm_ = cdm

        if cdm_device and not getattr(cdm_, "cdm", None) or cdm_device and reset:
            cdm_.cdm = cdm
            cdm_.cdm = cdm_device

    def globalize(self):
        self = cdm_
        return self
