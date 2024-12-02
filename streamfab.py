import os
import base64
import hashlib
import subprocess
from pathlib import Path
from Crypto.Cipher import AES

from widevinely.utils import logger
from widevinely.utils.exceptions import *

log = logger.getLogger("StreamFabModule")

EMAIL = "vugtmed@tipsehat.click"
MAC_ADDRESS = "8a-7a-b8-24-8f-d7"


class StreamFab:
    def cache(title, track, session, service):
        config = StreamFab.endpoints().get(service.cli.name) or {}
        region = "pm" if service.cli.name == "Prime Video" else "us"

        for service_, values in StreamFab.endpoints().items():
            if service_ == service.cli.name:
                config = values or {}
                break

        if config and config.get("cache"):
            cached = session.post(
                url=config["cache"].format(region=region),
                data={
                    "cmd": "downloadcheck",
                    "table": config["table"].format(region=region),
                    "kid": track.kid,
                    "ver": 20,
                    "email": EMAIL,
                    "wid": 1,
                    "pid": title.id,
                    "client_id": 95,
                    "reg_type": "register",
                    "machine_id": MAC_ADDRESS,
                    "app_version": 6104,
                },
            ).json()

            if cached["ret"] == "success":
                return StreamFab.decrypt(1, cached["k"], cached["d"], title.id, session)

        return None

    def Cdm(title, track, session, service, certificate):
        config = StreamFab.endpoints().get(service.cli.name) or {}

        """ Initializing Challenge """
        challenge = StreamFab.request(
            url=(
                "https://deuhd.ru/v1/st/"
                if service.cli.name != "DisneyPlus"
                else "https://ssl-jp.dvdfab.cn/ak/v2/st/"
            ),
            data={
                "T": 10,
                "B": 6,
                "C": EMAIL,
                "D": "",
                "E": "register",
                "F": "",
                "G": 95,
                "H": MAC_ADDRESS,
                "I": 1,
                "Z": 6104,
                "K": 2,
                "L": title.id,
                "M": track.pssh_b64,
                "N": certificate,
            },
            session=session,
        )["FB"]

        if service.cli.name != "DisneyPlus":
            """Signing challenge with latest ChromeCdm"""
            challenge = StreamFab.request(
                url="https://drm-w-j2.dvdfab.cn/mk/",
                data={
                    "T": 12,
                    "B": 6,
                    "C": EMAIL,
                    "E": "register",
                    "G": 95,
                    "H": MAC_ADDRESS,
                    "I": 1,
                    "Z": 6104,
                    "K": 2,
                    "L": title.id,
                    "M": challenge,
                },
                session=session,
            )["FB"]

        """ License request with the signed challenge """
        challenge = base64.b64decode(challenge.encode("utf8"))
        license_request = service.license(
            challenge=challenge,
            title=title,
            track=track,
            session_id=b"0",
        )

        if not isinstance(challenge, str):
            challenge = base64.b64encode(challenge).decode("utf-8")
        if not isinstance(license_request, str):
            license_request = base64.b64encode(license_request).decode("utf-8")

        if service.cli.name != "DisneyPlus":
            """Signing the license response with latest ChromeCdm"""
            if license_request:
                ML_request = StreamFab.request(
                    url="https://drm-w-j2.dvdfab.cn/ml/",
                    data={
                        "T": 15,
                        "B": 6,
                        "C": EMAIL,
                        "D": "",
                        "E": "register",
                        "F": "",
                        "G": 95,
                        "H": MAC_ADDRESS,
                        "I": 1,
                        "Z": 6104,
                        "K": 1,
                        "L": title.id,
                        "M": license_request,
                    },
                    session=session,
                )
                license_request = ML_request["FB"]
            else:
                log.exit(
                    f"Request was rejected by the License Server of {service.cli.name!r}."
                )

        """ Getting keys by parsing the license response """
        licensed = StreamFab.request(
            url=(
                "https://deuhd.ru/v1/li/"
                if service.cli.name != "DisneyPlus"
                else f"https://{config.get('cdn') or 'ssl-ca'}.dvdfab.cn/ak/v2/st/"
            ),
            data={
                "T": 11 if service.cli.name == "DisneyPlus" else 12,
                "B": 6,
                "C": EMAIL,
                "D": "",
                "E": "register",
                "F": "",
                "G": 95,
                "H": MAC_ADDRESS,
                "I": 1,
                "Z": 6104,
                "K": 3 if service.cli.name == "DisneyPlus" else 1,
                "L": title.id,
                "M": track.pssh_b64,
                "N": challenge,
                "O": license_request,
                "P": ML_request["D"],
            },
            session=session,
        )

        if licensed["R"] != "0":
            log.exit(f"Failed to get keys for KID {track.kid!r}")

        return StreamFab.decrypt(0, licensed["T"], licensed["D"], title.id, session)

    def decrypt(kv_id, enc_key, key_data, title_id, session):
        modkey2key = str(Path(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))) / "utils/modkey2key.exe")

        if kv_id == 1:
            data = f'{EMAIL}_SSKF_V1'
        else:
            data = f'{EMAIL}_SSKF_V1{MAC_ADDRESS}{title_id}'
            
        tok = hashlib.md5(data.encode("utf-8")).digest().hex()

        if os.name == "posix":
            mod_args = ["wine"]
        else:
            mod_args = []
        
        mod_args += [modkey2key, enc_key, tok]
        mod = subprocess.Popen(mod_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        key = mod.stdout.readline().strip().splitlines()[0].decode()
        mod.terminate()
        
        cipher = AES.new(key.upper()[:16].encode(), mode=AES.MODE_ECB)
        decrypted_keys = cipher.decrypt(base64.b64decode(key_data)).decode()
        keys = decrypted_keys.split("|" if "|" in decrypted_keys else "\n")

        content_keys = {}
        for i, key in enumerate(keys):
            if key[:1].isalpha() or key[:1].isdigit():
                key = key.split(":")
                content_keys[key[0][:32]] = key[1][:32]

        return content_keys

    def request(url, data, session):
        for count in range(1, 10):
            try:
                req = session.post(url=url, data=data, timeout=4).json()
                if req["R"] == "0":
                    return req
            except Exception:
                if count == 9:
                    raise FailedLicensing

    def endpoints():
        return {
            "Amazon": {  # H264/H265 1080p SDR
                "cache": "https://drm-u1.dvdfab.cn/ak/pc/amazon/{region}/",
                "table": "amazon_{region}_keys",
                "cdn": "ssl-ca",
            },
            "AppleTVPlus": {  # H264/H265 576p SDR
                "cache": "https://drm-u1.dvdfab.cn/ak/re/appletv/",
                "table": "appletv_keys",
                "cdn": "ssl-ca",
            },
            "DiscoveryPlus": {  # Need Testing
                "cache": "https://drm-u1.dvdfab.cn/ak/pc/discovery/",
                "table": "discovery_keys",
                "cdn": "ssl-ca",
            },
            "DisneyPlus": {  # H264/H265 720p SDR
                "cache": "https://drm-u1.dvdfab.cn/ak/re/disneyplus/{region}/",
                "table": "disneyplus_{region}_keys",
                "cdn": "ssl-jp",
            },
            "HBOMax": {  # H264/H265 720p, 1080p-2160p SDR-HDR10 on some titles from cache
                "cache": "https://drm-u1.dvdfab.cn/ak/pc/hbomax/",
                "table": "hbomax_keys",
                "cdn": "ssl-ca",
            },
            "Hulu": {  # H264/H265 SD-2160p SDR-HDR10
                "cache": "https://drm-u1.dvdfab.cn/ak/pc/hulu/us/",
                "table": "hulu_us_keys",  # I think it only has US?
                "cdn": "ssl-ca",
            },
            "Netflix": {  # H264/H265 MPL/HPL / HDR10 / Dolby Vision
                "cache": "https://drm-u1.dvdfab.cn/ak/pc/netflix/",
                "table": "netflix_keys",
                "cdn": "ssl-ca",
            },
            "ParamountPlus": {  # H264/H265 1080p SDR
                "cache": "https://drm-u1.dvdfab.cn/ak/pc/",
                "table": "paramount_keys",
                "cdn": "ssl-ca",
            },
            "PeacockTV": {  # H264/H265 1080p SDR
                "cache": "https://drm-u1.dvdfab.cn/ak/pc/peacock/",
                "table": "peacock_keys",
                "cdn": "ssl-ca",
            },
            "Prime Video": {  # H264/H265 1080p SDR
                "cache": "https://drm-u1.dvdfab.cn/ak/pc/amazon/{region}/",
                "table": "amazon_{region}_keys",
                "cdn": "ssl-ca",
            },
            "SkyShowtime": {  # H264/H265 1080p SDR
                "cache": "https://drm-u1.dvdfab.cn/ak/pc/skyshowtime/",
                "table": "skyshowtime_keys",
                "cdn": "ssl-ca",
            },
        }
