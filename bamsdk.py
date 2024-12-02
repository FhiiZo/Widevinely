from widevinely.utils.BamSDK.services.account import account
from widevinely.utils.BamSDK.services.content import content
from widevinely.utils.BamSDK.services.drm import drm
from widevinely.utils.BamSDK.services.media import media
from widevinely.utils.BamSDK.services.session import session
from widevinely.utils.BamSDK.services.token import token


class BamSdk:
    def __init__(self, endpoint, session_=None, region=None):
        self._session = session_
        self.region = region

        self.config = self._session.get(endpoint).json()
        self.application = self.config["application"]
        self.commonHeaders = self.config["commonHeaders"]
        self.account = account(self.config["services"]["account"], self._session)
        self.content = content(
            self.config["services"]["content"], self._session, self.region
        )
        self.drm = drm(self.config["services"]["drm"], self._session)
        self.media = media(self.config["services"]["media"], self._session)
        self.session = session(self.config["services"]["session"], self._session)
        self.token = token(self.config["services"]["token"], self._session)
