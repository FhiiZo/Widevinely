from typing import Optional
from widevinely.utils import logger

log = logger.getLogger("")


class TitleNotAvailable(Exception):
    """
    Raised when a title is not available
    """

    def __init__(self):
        pass


class NextTitle(Exception):
    """
    Raised when a title is finished downloading and there
    are still other titles in the linkfile for download available
    """

    def __init__(self):
        pass


class MetadataNotAvailable(Exception):
    """
    Raised when not able to load metadata.
    """

    def __init__(self, reason=None):
        log.exit(f"\nFailed to load title metadata{f': {reason}' if reason else ''}")


class ManifestNotAvailable(Exception):
    """
    Raised when not able to load manifest.
    """

    def __init__(self, reason=None):
        log.exit(f"\nFailed to load content manifest{f': {reason}' if reason else ''}")


class NotEntitled(Exception):
    """
    Raised when user is not entitled
    to download the content.
    """

    def __init__(self):
        log.exit("\nUser is not entitled to download the content provided.")


class NoWanted(Exception):
    """
    Raised when Titles returns empty
    after using command '--wanted'.
    """

    def __init__(self):
        log.exit("\nCould not find the requested seasons or episodes.")


class TitleIsPreorder(Exception):
    """
    Raised when title is only available for preorder
    and user is not able to download the content yet.

    Region will be used if title could already
    be available in another country/region.
    """

    def __init__(self, region=False):
        log.exit(
            "Title is only available as preorder"
            f"{' in this region ' if region else ' '}"
            "at the moment."
        )


class CredentialsNotProvided(Exception):
    """
    Raised when user did not
    provide credentials.
    """

    def __init__(self):
        log.exit("Credentials are required but none were provided.")


class InvalidCredentials(Exception):
    """
    Raised when user provides
    invalid credentials.
    """

    def __init__(self):
        log.exit("Provided credentials seems to be invalid.")


class CookiesNotProvided(Exception):
    """
    Raised when user did not
    provide cookies.
    """

    def __init__(self):
        log.exit("Cookies are required but none were provided.")


class InvalidCookies(Exception):
    """
    Raised when user provides
    invalid or outdated cookies.
    """

    def __init__(self):
        log.exit("Provided cookies seems to be invalid or outdated.")


class TokenNotObtained(Exception):
    """
    Raised when requested token_type
    could not be obtained or has
    returned with an error.
    """

    def __init__(
        self,
        access_token: Optional[bool] = False,
        refresh_token: Optional[bool] = False,
        reason: Optional[str] = None,
    ):
        if access_token:
            log.exit(
                f"Was not able to obtain Access Token{f': {reason}' if reason else ''}"
            )
        elif refresh_token:
            log.exit(
                f"Was not able to refresh Access Token{f': {reason}' if reason else ''}"
            )
        else:
            log.exit(
                f"Was not able to obtain Token with unknown type{f': {reason}' if reason else '.'}"
            )


class TokenNotRefreshed(Exception):
    """
    Raised when requested token_type
    could not be refreshed or has
    returned with an error.
    """

    def __init__(
        self,
        reason: Optional[str] = None,
    ):
        log.exit(f"\nWas not able to refresh Token{f': {reason}' if reason else '.'}")


class GeoRestriction(Exception):
    """
    Raised when streaming service or title
    is not available in current region
    """

    def __init__(self):
        log.exit("\nThis title is not available in your country or region.")


class VPN_PROXY_DETECTED(Exception):
    """
    Raised when streaming service
    detects a VPN or Proxy service
    """

    def __init__(self):
        log.exit("\nVPN or Proxy service has been detected by the streaming service.")


class ProxyConnectionError(Exception):
    """
    Raised when it was not able to
    connect with the provided proxy uri
    """

    def __init__(self, type_, uri):
        log.exit(f"\nCould not connect with {type_} proxy {uri!r}.")


class FailedLicensing(Exception):
    """
    Raised when a license request
    was not successful
    """

    def __init__(self, reason=None):
        log.exit(
            f"Could not complete license request{f': {reason}' if reason else '.'}"
        )


class CdmNotCapable(Exception):
    """
    Raised when a Cdm is not capable of licensing
    and will print it's capability, if known.
    """

    def __init__(self, non_whitelisted=False, downgraded=False, capability=None):
        if non_whitelisted and not downgraded and capability:
            log.exit(
                f"This Cdm does not seem to be whitelisted\nIt can only be used for content upto {capability}."
            )
        elif non_whitelisted and downgraded and capability:
            log.exit(
                f"This Cdm seems to be downgraded\nIt can only be used for content upto {capability}."
            )
        elif not non_whitelisted and not downgraded and capability:
            log.exit(
                f"This Cdm is only able to license content upto {capability}.\nIt requires a higher security level for content better than this."
            )
        else:
            log.exit("This Cdm is not capable of licensing this type content.")


class CdmBlacklisted(Exception):
    """
    Raised when a Cdm is not capable of licensing
    because it has been blacklisted by the streaming service.
    """

    def __init__(self):
        log.exit("This Cdm seems to be blacklisted by the streaming service.")


class WidevineVmpError(Exception):
    """
    Raised when ChromeCdm is being used but the service
    requires a VMP blob which is not provided.
    """

    def __init__(self):
        log.exit(
            "This service requires a VMP blob when using a ChromeCdm but none is provided."
        )
