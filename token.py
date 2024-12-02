import httpx

from typing import Optional
from widevinely.utils.BamSDK.services import Service


# noinspection PyPep8Naming
class token(Service):
    def __init__(self, cfg: dict, session: Optional[httpx.Client] = None):
        super().__init__(cfg, session)
        self.subject_tokens = self.extras["subjectTokenTypes"]

    def exchange(self, data: dict, api_key: str) -> dict:
        endpoint = self.client.endpoints["exchange"]
        return self.session.request(
            method=endpoint.method,
            url=endpoint.href,
            headers=endpoint.get_headers(apiKey=api_key),
            data=data,
        ).json()
