import json

from typing import Union
from widevinely.utils import logger
from widevinely.utils.exceptions import *
from widevinely.utils.BamSDK.services import Service

log = logger.getLogger("BAMSDK.drm")


# noinspection PyPep8Naming
class drm(Service):
    def widevineCertificate(self) -> Union[bytes, bytearray]:
        endpoint = self.client.endpoints["widevineCertificate"]
        return self.session.request(
            method=endpoint.method, url=endpoint.href, headers=endpoint.headers
        ).content

    def widevineLicense(
        self, license: Union[bytes, bytearray], access_token: str
    ) -> bytes:
        endpoint = self.client.endpoints["widevineLicense"]
        res = self.session.request(
            method=endpoint.method,
            url=endpoint.href,
            headers=endpoint.get_headers(accessToken=access_token),
            data=license,
        )

        try:
            # if it's json content, then an error occurred
            res = json.loads(res.text)
            error_code = res["errors"][0]["code"]
            try:
                error_description = res["errors"][0]["description"]
            except KeyError:
                pass
            if "widevine-vmp-error" in error_code:
                raise WidevineVmpError
            if "downgrade" in error_code or "capability" in error_description:
                return error_description
            elif (
                "throttled" in error_code
                or "bad-license-request" in error_code
                and "DRM_DEVICE_CERTIFICATE_SERIAL_NUMBER_REVOKED"
                in error_description
                or "bad-license-request" in error_code
                and 'drm-unique-id-has-been-revoked-in-device-certificate-status-list.'
                in error_description
            ):
                attempts = 0
                while attempts < 10:
                    res = self.session.request(
                        method=endpoint.method,
                        url=endpoint.href,
                        headers=endpoint.get_headers(accessToken=access_token),
                        data=license,
                    )
                    try:
                        res = json.loads(res.text)
                        attempts += 1
                    except json.JSONDecodeError:
                        return res.content
                if "throttled" in error_code:
                    log.exit(
                        " x DisneyPlus is throttling our connection with the License Server"
                    )
                elif "bad-license-request" in error_code:
                    log.exit(
                        " x This CDM seems to be revoked, but it could still work if you try it again"
                    )
            else:
                log.exit(f" x Failed to obtain license: {res}")
        except json.JSONDecodeError:
            return res.content
