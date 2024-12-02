from typing import Optional

from widevinely.utils import logger
from widevinely.utils.exceptions import *
from widevinely.utils.BamSDK.services import Service

log = logger.getLogger("BAMSDK.media")


# noinspection PyPep8Naming
class media(Service):
    def __init__(self, cfg, session=None):
        super().__init__(cfg, session)
        self.uhd_allowed = (
            True if not self.extras["isContentAccessRestricted"] else False
        )
        self.default_scenario = f"{self.extras['playbackEncryptionDefault']}-{self.extras['mediaQualityDefault']}"
        self.security_requirements = self.extras["securityCheckRequirements"]

    def mediaPayload(
        self,
        media_id,
        scenario,
        region,
        tokens,
        dsnp_self,
        retry: Optional[bool] = False,
    ):
        endpoint = self.client.endpoints["mediaPayload"]
        endpoint.headers.update(
            {"Authorization": tokens.get("accessToken") or tokens.get("access_token")}
        )

        res = self.session.request(
            method="GET",
            url=f"{self.client.baseUrl}/media/{media_id}/scenarios/{scenario}",
            headers=endpoint.headers,
        ).json()

        if "errors" in res:
            from widevinely.services.disneyplus import DisneyPlus
            error = res["errors"][0]["code"]
            
            if error == "blackout":
                raise GeoRestriction
            elif error == "not-entitled":
                raise NotEntitled
            elif error == "access-token.invalid":
                if retry:
                    raise TokenNotRefreshed

                # Refresh tokens and retry
                self.mediaPayload(
                    media_id,
                    scenario,
                    region,
                    tokens=DisneyPlus.configure(dsnp_self),
                    dsnp_self=dsnp_self,
                    retry=True,
                )
            else:
                raise ManifestNotAvailable(reason=res["errors"][0])
        return res
