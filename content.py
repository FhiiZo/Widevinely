from widevinely.utils.BamSDK.services import Service
from widevinely.utils.BamSDK.services import regions
from widevinely.utils.exceptions import *


# noinspection PyPep8Naming
class content(Service):
    def __init__(self, content, session, region_):
        self.client = content["client"]
        self.session = session
        self.regions = regions.REGION_MAP
        if region_ in self.regions:
            current_region = self.regions.index(region_)
            self.regions[0], self.regions[current_region] = (
                self.regions[current_region],
                self.regions[0],
            )
            if region_ != "NL":
                second_region = self.regions.index("NL")
                self.regions[1], self.regions[second_region] = (
                    self.regions[second_region],
                    self.regions[1],
                )

    def getMeta(self, regions, type, media_id):
        meta = {"title": {}, "description": {}}
        meta_type = "program" if type == "Video" else "series"
        for region in regions:
            endpoint = self.client["endpoints"][f"getDmc{type}Meta"]
            res = self.session.request(
                method=endpoint["method"],
                url=endpoint["href"].format(
                    apiVersion="5.1",
                    region=region,
                    kidsModeEnabled=False,
                    impliedMaturityRating=9999,
                    appLanguage=region.lower(),
                    encodedSeriesId=media_id,
                    encodedFamilyId=media_id,
                ),
            ).json()
            if res["data"][f"Dmc{type}Meta"][type.lower()]:
                lang = res["data"][f"Dmc{type}Meta"][type.lower()]["text"][
                    "description"
                ]["full"][meta_type]["default"]["language"][:2]
                if not meta or not any(lang in x for x in meta):
                    meta["title"][lang] = res["data"][f"Dmc{type}Meta"][type.lower()][
                        "text"
                    ]["title"]["full"][meta_type]["default"]["content"]
                    meta["description"][lang] = res["data"][f"Dmc{type}Meta"][
                        type.lower()
                    ]["text"]["description"]["full"][meta_type]["default"]["content"]
        
        try:
            meta["cast"] = [
                x["displayName"]
                for x in res["data"][f"Dmc{type}Meta"][type.lower()]["participants"]
                if x["role"] == "Actor"
            ]
            meta["releaseYear"] = res["data"][f"Dmc{type}Meta"][type.lower()]["releases"][
                0
            ]["releaseYear"]
        except Exception:
            raise MetadataNotAvailable
        
        return meta

    def getBundle(self, region_, type, media_id, title_found=False, first_failed=False):
        DmcBundle = []
        if self.regions[0] != region_:
            current_region = self.regions.index(region_)
            self.regions[0], self.regions[current_region] = (
                self.regions[current_region],
                self.regions[0],
            )

        for portability in self.regions:
            if title_found:
                portability = self.regions[self.regions.index(portability) - 1]
                break

            endpoint = self.client["endpoints"][f"getDmc{type}Bundle"]
            for appLanguage in ["en", portability.lower()]:
                if first_failed:
                    continue

                res = self.session.request(
                    method=endpoint["method"],
                    url=endpoint["href"].format(
                        apiVersion="5.1",
                        region=portability,
                        kidsModeEnabled=False,
                        impliedMaturityRating=9999,
                        appLanguage=appLanguage,
                        encodedSeriesId=media_id,
                        encodedFamilyId=media_id,
                    ),
                ).json()

                if not res["data"][f"Dmc{type}Bundle"][type.lower()]:
                    first_failed = False
                    continue

                title_found = True
                DmcBundle.append(res["data"][f"Dmc{type}Bundle"])

        return DmcBundle, portability

    def getDmcEpisodes(
        self, region_, season_id, page, title_found=False, first_failed=False
    ):
        DmcEpisodes = []
        for portability in self.regions:
            if title_found:
                portability = self.regions[self.regions.index(portability) - 1]
                break

        endpoint = self.client["endpoints"]["getDmcEpisodes"]
        for appLanguage in ["en", portability.lower()]:
            if first_failed:
                continue

            res = self.session.request(
                method=endpoint["method"],
                url=endpoint["href"].format(
                    apiVersion="5.1",
                    region=region_,
                    kidsModeEnabled=False,
                    impliedMaturityRating=9999,
                    appLanguage=appLanguage,
                    seasonId=season_id,
                    pageSize=15,
                    page=page,
                ),
            ).json()

            if not res["data"]["DmcEpisodes"]:
                first_failed = False
                continue

            title_found = True
            DmcEpisodes.append(res["data"]["DmcEpisodes"])

        return DmcEpisodes
