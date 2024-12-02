from widevinely.utils.BamSDK.services import Service


# noinspection PyPep8Naming
class bamIdentity(Service):
    def identityLogin(self, email: str, password: str, access_token: str) -> dict:
        endpoint = self.client.endpoints["identityLogin"]
        return self.session.request(
            method=endpoint.method,
            url=endpoint.href,
            headers=endpoint.get_headers(accessToken=access_token),
            json={"email": email, "password": password},
        ).json()
