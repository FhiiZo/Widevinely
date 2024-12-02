import re
import os
import json
import httpx
import shutil
import random

from subprocess import run, PIPE
from urllib.parse import urlsplit

from widevinely.config import config, directories
from widevinely.utils import logger
from widevinely.utils.globals import arguments

log = logger.getLogger("proxies")


def get_proxy(type_, silence=False):
    args = arguments()
    if not args.dl.proxy[type_]:
        return

    if not args.dl.no_proxy:
        old_ip = httpx.get("https://ipinfo.io/json?token=115e801551c194").json()
        if not silence:
            log.info_("ACTIVATING PROXY", style="title")

        old_ip = (
            " - [content]OLD IP   [/content]"
            + f"{old_ip['ip']} ({old_ip['country'].upper()})"
        )

        if type(args.dl.proxy[type_]) == list or "http" in args.dl.proxy[type_] or "socks" in args.dl.proxy[type_]:
            if not silence:
                log.info_(old_ip)
            return fix_proxy(
                (
                    random.choice(args.dl.proxy[type_])
                    if type(args.dl.proxy[type_]) == list
                    else args.dl.proxy[type_]
                )
            )

        if config.proxies.get("uri") and config.proxies["uri"].get(
            args.dl.proxy[type_]
        ):
            if not silence:
                log.info_(old_ip)
            return fix_proxy(
                (
                    random.choice(config.proxies["uri"][args.dl.proxy[type_]])
                    if type(config.proxies["uri"][args.dl.proxy[type_]]) == list
                    else config.proxies["uri"][args.dl.proxy[type_]]
                )
            )

        if args.dl.proxy_service:
            if not config.proxies.get("accounts"):
                log.exit(
                    "\nProxy service provided but could not find any account in configuration file."
                )

            if args.dl.proxy_service not in [
                "NordVPN",
                "PrivateVPN",
                "HolaVPN",
                "Torguard",
            ]:
                log.exit(
                    f"Proxy service {args.dl.proxy_service!r} is not known or not supported yet.\n"
                    "Available proxy services: 'NordVPN', 'PrivateVPN', 'HolaVPN' and 'Torguard'."
                )

            if not silence:
                log.info_(" - [content]SERVICE  [/content]" + args.dl.proxy_service)
                log.info_(old_ip)

            return fix_proxy(
                globals()[args.dl.proxy_service].get_proxy(args.dl.proxy[type_])
            )

    return None


def fix_proxy(proxy):
    proxy_parts = urlsplit(proxy, allow_fragments=True)
    if proxy_parts.username and proxy_parts.password:
        proxy = re.sub(
            proxy_parts.username, proxy_parts.username.replace("@", "%40"), proxy
        )
        proxy = re.sub(
            proxy_parts.password, proxy_parts.password.replace("@", "%40"), proxy
        )

    return proxy


class NordVPN:
    def get_proxy(country):
        credentials = config.proxies["accounts"].get("NordVPN") or config.proxies.get(
            "nordvpn"
        )
        if not credentials:
            log.exit("Could not find NordVPN credentials in configuration file.")

        proxy = f"socks5://{credentials}@"
        if "." in country:  # Direct server hostname
            proxy += country
        else:
            hostname = NordVPN.servers().get(country)
            if not hostname:
                log.exit(f"NordVPN does not provide a server for country {country!r}")
            proxy += hostname
        return proxy + ":1080"

    def servers():
        return {
            "nl": "nl.socks.nordhold.net",  # Netherlands [DEFAULT]
            "nl-ams": "amsterdam.nl.socks.nordhold.net",  # Netherlands - Amsterdam
            "us": "us.socks.nordhold.net",  # USA [DEFAULT]
            "us-atl": "atlanta.us.socks.nordhold.net",  # USA - Atlanta
            "us-dal": "dallas.us.socks.nordhold.net",  # USA - Dallas
            "us-la": "los-angeles.us.socks.nordhold.net",  # USA - Los Angeles
            "ie": "ie.socks.nordhold.net",  # Ireland [DEFAULT]
            "ie-dub": "dublin.ie.socks.nordhold.net",  # Ireland - Dublin
            "se": "se.socks.nordhold.net",  # Sweden [DEFAULT]
            "se-sto": "stockholm.se.socks.nordhold.net",  # Sweden - Stockholm
        }


class PrivateVPN:
    def get_proxy(country):
        credentials = config.proxies["accounts"].get(
            "PrivateVPN"
        ) or config.proxies.get("privatevpn")
        if not credentials:
            log.exit("Could not find PrivateVPN credentials in configuration file.")

        proxy = f"http://{credentials}@"
        if "." in country:  # Direct server hostname
            proxy += country
        else:
            hostname = PrivateVPN.servers().get(country)
            if not hostname:
                log.exit(
                    f"PrivateVPN does not provide a server for country {country!r}"
                )
            proxy += hostname + ".pvdata.host"
        return proxy + ":8080"

    def servers():
        return {
            "ar": "ar-bue",  # Argentina - Buenos Aires (Virtual)
            "au-bri": "au-bri",  # Australia - Brisbane
            "au-per": "au-bri",  # Australia - Perth
            "au": "au-mel",  # Australia - Melbourne [DEFAULT]
            "au-syd": "au-syd",  # Australia - Sydney
            "at": "at-wie",  # Austria - Wien
            "be": "be-bru",  # Belgium - Brussels
            "br": "br-sao",  # Brazil - Sao Paulo
            "bg": "bg-sof",  # Bulgaria - Sofia
            "ca-mon": "ca-mon",  # Canada - Montreal
            "ca": "ca-tor",  # Canada - Toronto [DEFAULT]
            "ca-van": "ca-van",  # Canada - Vancouver
            "cl": "cl-san",  # Chile - Santiago (Virtual)
            "co": "co-bog",  # Colombia - Bogotá (Virtual)
            "cr": "cr-san",  # Costa Rica - San Jose
            "hr": "hr-zag",  # Croatia - Zagreb
            "cy": "cy-nic",  # Cyprus - Limassol
            "cz": "cz-pra",  # Czech Republic - Prague
            "dk": "dk-cop",  # Denmark - Copenhagen
            "fi": "fi-esp",  # Estonia- Tallinn
            "fr": "fr-par",  # Finland - Espoo
            "de": "de-ber",  # Germany - Berlin [DEFAULT]
            "de-fra": "de-fra",  # Germany - Frankfurt
            "gr": "gr-ath",  # Greece - Athens
            "hk": "hk-hon",  # Hong Kong
            "hk-chi": "hk-china",  # Hong Kong - China route
            "hu": "hu-bud",  # Hungary - Budapest
            "is": "is-rey",  # Iceland - Reykjavik
            "in-ban": "in-ban",  # India - Bangalore (Virtual)
            "in": "in-mum",  # India - Mumbai [DEFAULT]
            "id": "id-jak",  # Indonesia - Jakarta
            "ie": "ie-dub",  # Ireland - Dublin
            "im": "im-bal",  # Isle of Man - Ballasalla
            "il": "il-tel",  # Israel - Tel Aviv
            "it": "it-mil",  # Italy - Milan
            "jp": "jp-tok",  # Japan - Tokyo
            "lv": "lv-rig",  # Latvia - Riga
            "lt": "lt-sia",  # Lithuania - Siauliai
            "lu": "lu-ste",  # Luxembourg - Luxembourg City
            "my": "my-kua",  # Malaysia - Kuala Lumpur
            "mt": "mt-qor",  # Malta - Qormi
            "mx": "mx-mex",  # Mexico - Mexico City (Virtual)
            "md": "md-chi",  # Moldova - Chisinau
            "nl": "nl-ams",  # Netherlands - Amsterdam
            "nz": "nz-auc",  # New Zealand - Auckland
            "ng": "ng-lag",  # Nigeria - Lagos
            "no": "no-osl",  # Norway - Oslo
            "pa": "pa-pan",  # Panama - Panama City (Virtual)
            "pe": "pe-lim",  # Peru - Lima(Virtual)
            "ph": "ph-man",  # Philippines - Manila
            "pl": "pl-tor",  # Poland - Torun
            "pt": "pt-lis",  # Portugal - Lisbon
            "ro": "ro-buk",  # Romania - Bukarest
            "ru-kra": "ru-kra",  # Russia - Krasnoyarsk
            "ru": "ru-mos",  # Russia - Moscow [DEFAULT]
            "rs": "rs-bel",  # Serbia - Belgrader
            "sg": "sg-sin",  # Singapore
            "sk": "sk-bra",  # Slovakia - Bratislava
            "za": "za-joh",  # South Africa - Johannesburg
            "kr": "kr-seo",  # South Korea - Seoul
            "es": "es-mad",  # Spain - Madrid
            "se-got": "se-got",  # Sweden - Gothenburg
            "se-kis": "se-kis",  # Sweden - Kista
            "se": "se-sto",  # Sweden - Stockholm [DEFAULT]
            "ch": "ch-zur",  # Switzerland - Zürich
            "tw": "tw-tai",  # Taiwan - Taipei
            "th": "th-ban",  # Thailand - Bangkok
            "tr": "tr-ist",  # Turkey - Istanbul
            "uk": "uk-lon",  # United Kingdom - London
            "uk-man": "uk-man",  # United Kingdom - Manchester
            "ua": "ua-nik",  # Ukraine - Nikolaev
            "ae": "ae-dub",  # United Arab Emirates - Dubai
            "us-atl": "us-atl",  # USA - Atlanta
            "us-buf": "us-buf",  # USA - Buffalo
            "us-chi": "us-chi",  # USA - Chicago
            "us-dal": "us-dal",  # USA - Dallas
            "us-las": "us-las",  # USA - Denver
            "us-los": "us-los",  # USA - Las Vegas
            "us-mia": "us-mia",  # USA - Miami
            "us-jer": "us-jer",  # USA - New Jersey
            "us": "us-nyc",  # USA - New York [DEFAULT]
            "us-pho": "us-pho",  # USA - Phoenix
            "vn": "vn-hoc",  # Vietnam - Ho Chi Minh City
        }


class HolaVPN:
    def get_proxy(country):
        exec_ = shutil.which("hola-proxy")
        if not exec_:
            log.exit("Binary 'hola-proxy' could not be found in PATH.")

        cache = HolaVPN.get_cache(country)
        if cache:
            return random.choice(cache)

        proxy = "http://{credentials}@{hostname}:22222"
        for proxy_type in ("lum", "direct"):
            hola = run(
                [
                    exec_,
                    "-country",
                    country if "." not in country else country.split(".")[0],
                    "-list-proxies",
                    "-limit",
                    "3",
                    "-proxy-type",
                    proxy_type,
                ],
                stdout=PIPE,
                stderr=PIPE,
                text=True,
            )
            if hola.returncode:
                log.exit(f"Could not get a HolaVPN server for country {country!r}")

            proxies = []
            hola = hola.stdout.split("\n")
            user_uuid = hola[0].replace("Login: ", "")
            password = hola[1].replace("Password: ", "")
            for line in hola:
                if "22222" in line:
                    proxies += [line.split(",")[0] if "." not in country else country]

            for proxy_ in proxies:
                proxies[proxies.index(proxy_)] = proxy.format(
                    credentials=f"{user_uuid}:{password}", hostname=proxy_
                )

            if proxies:
                break

        return random.choice(HolaVPN.update_cache(country, proxies))

    def get_cache(country):
        if not os.path.isfile(directories.holavpn_cache):
            return

        cache = json.loads(directories.holavpn_cache.read_text(encoding="utf8"))

        return cache["countries"][country] if cache["countries"].get(country) else None

    def update_cache(country, proxies, cache={"countries": {}}):
        if os.path.isfile(directories.holavpn_cache):
            cache = json.loads(directories.holavpn_cache.read_text(encoding="utf8"))

        cache["countries"][country] = proxies

        with open(directories.holavpn_cache, "w+") as cache_file:
            cache_file.write(json.dumps(cache, indent=3))

        return cache["countries"][country]


class Torguard:
    def get_proxy(country):
        credentials = config.proxies["accounts"].get("Torguard") or config.proxies.get(
            "torguard"
        )
        if not credentials:
            log.exit("Could not find Torguard credentials in configuration file.")

        proxy = f"socks5://{credentials}@"
        if "." in country:  # Direct server hostname
            proxy += country
        else:
            hostname = random.choice(Torguard.servers().get(country))
            if not hostname:
                log.exit(f"Torguard does not provide a server for country {country!r}")
            proxy += hostname

        return proxy + ":1080"

    def servers():
        return {
            "ca": [  # Canada - Montreal 89.xx, 86.xx, 146.xx, 176.xx | Toronto 68.xx.xx.xx
                "89.47.234.26",
                "89.47.234.74",
                "86.106.90.226",
                "146.70.27.218",
                "146.70.27.242",
                "146.70.27.250",
                "176.113.74.138",
                "176.113.74.74",
                "176.113.74.130",
                "68.71.244.2",
                "68.71.244.6",
                "68.71.244.10",
                "68.71.244.18",
                "68.71.244.22",
                "68.71.244.26",
                "68.71.244.30",
                "68.71.244.34",
                "68.71.244.38",
                "68.71.244.42",
                "68.71.244.46",
                "68.71.244.50",
                "68.71.244.54",
                "68.71.244.58",
                "68.71.244.62",
                "68.71.244.66",
                "68.71.244.70",
                "68.71.244.78",
                "68.71.244.82",
                "68.71.244.90",
                "68.71.244.94",
                "68.71.244.98",
                "68.71.244.102",
            ],
            "nl": ["206.217.216.4", "206.217.216.8"],  # Netherlands - Amsterdam
            "uk": ["146.70.95.26", "146.70.95.74"],  # United Kingdom - London
        }
