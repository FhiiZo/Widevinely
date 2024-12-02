import re
import click
import importlib

from typing import Optional

from widevinely import services
from widevinely.utils import logger
from widevinely.services.BaseService import BaseService
from widevinely.utils.collections import as_list

log = logger.getLogger("click")


class ContextData:
    def __init__(
        self,
        config,
        vaults,
        cdm,
        service_cdm=None,
        profile=None,
        cookies=None,
        credentials=None,
    ):
        self.config = config
        self.vaults = vaults
        self.cdm = cdm
        self.service_cdm = service_cdm
        self.profile = profile
        self.cookies = cookies
        self.credentials = credentials


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            setattr(
                services,
                cmd_name,
                getattr(
                    importlib.import_module(f"widevinely.services.{cmd_name.lower()}"),
                    cmd_name,
                ),
            )
            return rv

        for key, aliases in services.SERVICE_MAP.items():
            if cmd_name.lower() in map(str.lower, aliases):
                setattr(
                    services,
                    key,
                    getattr(
                        importlib.import_module(f"widevinely.services.{key.lower()}"),
                        key,
                    ),
                )
                return click.Group.get_command(self, ctx, key)

        service = services.get_service_key(cmd_name)

        if not service:
            title_id = None

            for x in dir(services):
                x = getattr(services, x)

                if (
                    isinstance(x, type)
                    and issubclass(x, BaseService)
                    and x != BaseService
                ):
                    title_re = as_list(getattr(x, "TITLE_RE", []))
                    for regex in title_re:
                        m = re.search(regex, cmd_name)
                        if m and m.group().startswith(("http://", "https://", "urn:")):
                            title_id = m.group("id")
                            break

                if title_id:
                    ctx.params["service_name"] = x.__name__
                    setattr(
                        services,
                        x.__name__,
                        getattr(
                            importlib.import_module(
                                f"widevinely.services.{x.__name__.lower()}"
                            ),
                            x.__name__,
                        ),
                    )
                    importlib.import_module(f"widevinely.services.{x.__name__.lower()}")
                    ctx.params["title"] = cmd_name
                    return click.Group.get_command(self, ctx, x.__name__)

            if not title_id:
                log.exit(" - Unable to guess service from title ID")

    def list_commands(self, ctx):
        return sorted(self.commands, key=str.casefold)


def _choice(ctx, param, value, value_map):
    if value is None:
        return None

    if value.lower() in value_map:
        return value_map[value.lower()]
    else:
        log.exit(
            f"Argument {param.name!r} only accepts {list(x for x in value_map)}, not {value!r}."
        )


def proxy_service_param(ctx, param, value):
    return _choice(
        ctx,
        param,
        value,
        {
            "nordvpn": "NordVPN",
            "privatevpn": "PrivateVPN",
            "hola": "HolaVPN",
            "torguard": "Torguard",
        },
    )


def audio_codec(
    ctx: Optional[str] = "", param: Optional[str] = "", value: Optional[str] = ""
):
    return _choice(
        ctx,
        param,
        value,
        {
            "aac": "AAC",
            "mp4a": "AAC",
            "he": "HE-AAC",
            "he-aac": "HE-AAC",
            "xhe": "xHE-AAC",
            "xhe-aac": "xHE-AAC",
            "ac3": "AC3",
            "ac-3": "AC3",
            "dd": "AC3",
            "ec3": "EAC3",
            "ec-3": "EAC3",
            "eac": "EAC3",
            "eac3": "EAC3",
            "e-ac": "EAC3",
            "e-ac3": "EAC3",
            "e-ac-3": "EAC3",
            "dd+": "EAC3",
            "ddp": "EAC3",
            "dts": "DTS",
            "dts-core": "DTS",
            "vorb": "VORB",
            "vorbis": "VORB",
            "opus": "OPUS",
        },
    )


def audio_channels(
    ctx: Optional[str] = "", param: Optional[str] = "", value: Optional[str] = ""
):
    return _choice(
        ctx,
        param,
        value,
        {
            "2": "2.0",
            "2.0": "2.0",
            "5.1": "5.1",
            "6": "5.1",
            "7.1": "7.1",
            "atmos": "16/JOC",
            "16/joc": "16/JOC",
        },
    )


def language_param(ctx, param, value):
    if isinstance(value, list):
        return value
    if not value:
        return []
    return re.split(r"\s*[,;]\s*", value)


def video_quality(ctx, param, value):
    if not value:
        return None

    if value.lower() == "sd":
        return 576

    if value.lower() in ["4k", "uhd"]:
        return 2160

    try:
        return int(value.lower().rstrip("p"))
    except TypeError:
        log.exit(
            f"expected string for int() conversion, got {value!r} of type {value.__class__.__name__}",
            param,
            ctx,
        )
    except ValueError:
        log.exit(f"{value!r} is not a valid integer", param, ctx)


def video_range(ctx, param, value):
    return _choice(
        ctx,
        param,
        value,
        {
            "sdr": "SDR",
            "hevc": "SDR",
            "hdr": "HDR10",
            "hdr10": "HDR10",
            "hdr-dv": "HDR10+DV",
            "hdr+dv": "HDR10+DV",
            "hdr10-dv": "HDR10+DV",
            "hdr10+dv": "HDR10+DV",
            "hlg": "HLG",
            "dv": "DV",
            "dovi": "DV",
        },
    )


def video_codec(
    ctx: Optional[str] = "", param: Optional[str] = "", value: Optional[str] = ""
):
    return _choice(
        ctx,
        param,
        value,
        {
            "h264": "H.264",
            "h.264": "H.264",
            "avc": "H.264",
            "avc1": "H.264",
            "h265": "H.265",
            "h.265": "H.265",
            "hevc": "H.265",
            "hev1": "H.265",
            "hvc1": "H.265",
            "dvhe": "H.265",
            "dvh1": "H.265",
            "vp9": "VP9",
            "av1": "AV1",
        },
    )


def wanted_param(ctx, param, value):
    MIN_EPISODE = 0
    MAX_EPISODE = 9999

    def parse_tokens(*tokens):
        """
        Parse multiple tokens or ranged tokens as '{s}x{e}' strings.

        Supports exclusioning by putting a `-` before the token.

        Example:
            >>> parse_tokens("S01E01")
            ["1x1"]
            >>> parse_tokens("S02E01", "S02E03-S02E05")
            ["2x1", "2x3", "2x4", "2x5"]
            >>> parse_tokens("S01-S05", "-S03", "-S02E01")
            ["1x0", "1x1", ..., "2x0", (...), "2x2", (...), "4x0", ..., "5x0", ...]
        """
        if len(tokens) == 0:
            return []
        computed = []
        for token in tokens:
            # If wanted_param startswith - we want all seasons before -Sxx
            if token.startswith("-"):
                token = "S01" + token

            # If wanted_param endswith - we want all seasons after Sxx-
            if token.endswith("-"):
                token = token + "S30"  # 30 seasons enough?

            parsed = [
                re.match(r"^S(?P<season>\d+)(E(?P<episode>\d+))?$", x, re.IGNORECASE)
                for x in re.split(r"[:-]", token)
            ]
            if len(parsed) > 2:
                log.exit(
                    f"Invalid token, only a left and right range is acceptable: {token}"
                )
            if len(parsed) == 1:
                parsed.append(parsed[0])
            if any(x is None for x in parsed):
                log.exit(f"Invalid token, syntax error occurred: {token}")
            from_season, from_episode = [
                int(v) if v is not None else MIN_EPISODE
                for k, v in parsed[0].groupdict().items()
                if parsed[0]
            ]
            to_season, to_episode = [
                int(v) if v is not None else MAX_EPISODE
                for k, v in parsed[1].groupdict().items()
                if parsed[1]
            ]
            if from_season > to_season:
                log.exit(
                    f"Invalid range, left side season cannot be bigger than right side season: {token}"
                )
            if from_season == to_season and from_episode > to_episode:
                log.exit(
                    f"Invalid range, left side episode cannot be bigger than right side episode: {token}"
                )
            for s in range(from_season, to_season + 1):
                for e in range(
                    from_episode if s == from_season else 0,
                    (MAX_EPISODE if s < to_season else to_episode) + 1,
                ):
                    (computed).append(f"{s}x{e}")

        return list(set(computed))

    if value:
        return parse_tokens(*re.split(r"\s*[,;]\s*", value))
