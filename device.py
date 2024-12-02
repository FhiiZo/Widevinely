from json import JSONDecodeError
from widevinely.utils.BamSDK.services import Service
from widevinely.utils import logger

log = logger.getLogger("BAMSDK.services.device")


# noinspection PyPep8Naming
class device(Service):
    def createDeviceGrant(self, json: dict, api_key: str) -> dict:
        endpoint = self.client.endpoints["createDeviceGrant"]
        res = self.session.request(
            method=endpoint.method,
            url=endpoint.href,
            headers=endpoint.get_headers(apiKey=api_key),
            json=json,
        )

        try:
            data = res.json()
        except JSONDecodeError:
            Exception
            log.exit(
                f"An unexpected response occurred for bamsdk.createDeviceGrant: {res.text}"
            )
        return data
