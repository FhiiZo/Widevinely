from widevinely.utils.BamSDK.services import Service


# noinspection PyPep8Naming
class session(Service):
    def getInfo(self, access_token: str) -> dict:
        endpoint = self.client.endpoints["getInfo"]
        return self.session.request(
            method=endpoint.method,
            url=endpoint.href,
            headers=endpoint.get_headers(accessToken=access_token),
        ).json()

    def getLocation(self, access_token: str) -> dict:
        endpoint = self.client.endpoints["getLocation"]
        return self.session.request(
            method=endpoint.method,
            url=endpoint.href,
            headers=endpoint.get_headers(accessToken=access_token),
        ).json()
