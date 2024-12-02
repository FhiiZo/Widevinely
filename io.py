from __future__ import annotations

import os
import requests
import re
import sys
import yaml
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from widevinely.utils import logger
from widevinely.utils.collections import as_list

log = logger.getLogger("io")


def load_yaml(path):
    if not os.path.isfile(path):
        return {}
    with open(path) as fd:
        return yaml.safe_load(fd)


def get_ip_info(session: Optional[requests.Session] = None) -> dict:
    """Use ipinfo.io to get IP location information."""
    return (session or requests.Session()).get("https://ipinfo.io/json").json()


def download_range(
    url: str, count: int, start: int = 0, proxy: Optional[str] = None
) -> bytes:
    """Download n bytes without using the Range header due to support issues."""
    # TODO: Can this be done with Aria2c?
    executable = shutil.which("curl")
    if not executable:
        log.exit(
            " x Track needs curl to download a chunk of data but looks like curl is not installed"
        )

    arguments = [
        executable,
        "-s",  # use -s instead of --no-progress-meter due to version requirements
        "-L",  # follow redirects, e.g. http->https
        "--proxy-insecure",  # disable SSL verification of proxy
        "--output",
        "-",  # output to stdout
        "--url",
        url,
    ]
    if proxy:
        arguments.extend(["--proxy", proxy])

    curl = subprocess.Popen(
        arguments, stdout=subprocess.PIPE, stderr=open(os.devnull, "wb"), shell=False
    )
    buffer = b""
    location = -1
    while len(buffer) < count:
        stdout = curl.stdout
        data = b""
        if stdout:
            data = stdout.read(1)
        if len(data) > 0:
            location += len(data)
            if location >= start:
                buffer += data
        else:
            if curl.poll() is not None:
                break
    curl.kill()  # stop downloading
    return buffer


def scatchy(title, ctx, uri, out, headers=None):
    """
    Downloads file(s) using Scatchy.

    Parameters:
        uri: URL to download. If uri is a list of urls, they will be downloaded and
          concatenated into one file.
        out: The output file path to save to.
        headers: Headers to apply to Scatchy.
    """
    from widevinely.utils.globals import arguments

    args = arguments()

    out = Path(out)

    segmented = isinstance(uri, list)
    segments_dir = out.with_name(out.name + "_segments")
    uri_list_file = (
        out.parent / "uri_list.txt"
        if "TextTrack" not in out.name
        else out.parent / "segment_list.txt"
    )
    if segmented:
        with open(str(uri_list_file), "w+") as uri_list:
            uri_list.write(
                "\n".join([f"{url.replace('‾', '~')}" for i, url in enumerate(uri)])
            )

    executable = shutil.which("scatchy")
    if not executable:
        EnvironmentError
        log.exit("Scatchy executable not found...")

    arguments = executable
    if not segmented:
        arguments += f' "{uri}"'
        arguments += " --allow-overwrite"  # Continue downloading a partially downloaded file not supported yet
    else:
        arguments += " --continue"  # Continue downloading a partially downloaded file
        arguments += " --segments-dir"
        arguments += f' "{str(segments_dir)}"'

    arguments += " --output"
    arguments += f" {str(out.parent)}/{str(out.name)}"

    arguments += " --silence" if "TextTrack" not in out.name else " --quiet"

    for header, value in (headers or {}).items():
        if header.lower() == "accept-encoding":
            # we cannot set an allowed encoding, or it will return compressed
            # and the code is not set up to uncompress the data
            continue
        arguments += f' --header "{header}:{value}"'

    if segmented:
        arguments += " --input-file"
        arguments += f" {str(uri_list_file)}"

    if not args.dl.no_proxy and args.dl.proxy["download"]:
        arguments += " --proxy "
        arguments += args.dl.proxy["download"]

    if ctx.obj.cookies:
        arguments += " --cookies"
        arguments += f' "{ctx.obj.cookies.filename}"'

    track_download = subprocess.run(
        arguments,
        stdout=subprocess.PIPE if "TextTrack" in out.name else None,
        stderr=subprocess.PIPE,
        shell=True,
        text=True,
    )

    if segmented:
        os.remove(str(uri_list_file))

    if track_download.returncode:
        if not os.path.isfile(out):
            log.exit(f"   x {track_download.stderr}".rstrip("\r"))


def aria2c(title, uri, out, headers=None):
    """
    Downloads file(s) using Aria2(c).

    Parameters:
        uri: URL to download. If uri is a list of urls, they will be downloaded and
          concatenated into one file.
        out: The output file path to save to.
        headers: Headers to apply on aria2c.
        proxy: Proxy to apply on aria2c.
    """
    from widevinely.utils.globals import arguments

    args = arguments()

    out = Path(out)

    executable = shutil.which("aria2c") or shutil.which("aria2")
    if not executable:
        EnvironmentError
        log.exit("Aria2c executable not found...")

    arguments = executable
    arguments += " -c"  # Continue downloading a partially downloaded file
    arguments += " --remote-time"  # Retrieve timestamp of the remote file from the and apply if available
    arguments += (
        f" -o {out.name}"  # The file name of the downloaded file, relative to -d
    )
    arguments += (
        " -x 16"  # The maximum number of connections to one server for each download
    )
    arguments += " -j 16"  # The maximum number of parallel downloads for every static (HTTP/FTP) URL
    arguments += " -s 16"  # Download a file using N connections.
    arguments += " --allow-overwrite=true"
    arguments += " --auto-file-renaming=false"
    arguments += " --retry-wait 5"  # Set the seconds to wait between retries.
    arguments += " --max-tries 15"
    arguments += " --max-file-not-found 15"
    arguments += " --file-allocation"
    arguments += " none" if sys.platform == "win32" else " falloc"
    arguments += " --console-log-level warn"
    arguments += " --download-result=hide"
    arguments += " --summary-interval=0"
    arguments += " --http-auth-challenge=true "

    if not args.dl.no_proxy and args.dl.proxy["download"]:
        arguments += " --all-proxy="
        arguments += args.dl.proxy["download"]

    for header, value in (headers or {}).items():
        if header.lower() == "accept-encoding":
            # we cannot set an allowed encoding, or it will return compressed
            # and the code is not set up to uncompress the data
            continue
        arguments += f' --header "{header}:{value}"'

    segmented = isinstance(uri, list)
    segments_dir = out.with_name(out.name + "_segments")
    if segmented:
        uri = "\n".join(
            [
                f"{url.replace('‾', '~')}\n"
                f"\tdir={segments_dir}\n"
                f"\tout={i:08}.mp4"
                for i, url in enumerate(uri)
            ]
        )

    subprocess.run(
        arguments + f'-d "{str(segments_dir)}" -i-'
        if segmented
        else arguments + f' -d {str(out.parent)} "{uri}"',
        input=as_list(uri)[0] if segmented else None,
        stdout=subprocess.PIPE if "TextTrack" in out.name else None,
        stderr=subprocess.PIPE,
        shell=True,
        text=True,
    )

    if segmented:
        # merge the segments together
        with open(out, "wb") as f:
            for file in sorted(segments_dir.iterdir()):
                data = file.read_bytes()
                # Apple TV+ needs this done to fix audio decryption
                data = re.sub(
                    b"(tfhd\x00\x02\x00\x1a\x00\x00\x00\x01\x00\x00\x00)\x02",
                    b"\\g<1>\x01",
                    data,
                )
                f.write(data)
                file.unlink()  # delete, we don't need it anymore
        segments_dir.rmdir()

    if "TextTrack" not in out.name:
        log.info_("")

    if "TextTrack" not in out.name:
        if not os.path.isfile(out) or os.path.isfile(f"{out}.aria2"):
            log.exit(" x Download failed...                   ")


async def saldl(uri, out, headers=None):
    out = Path(out)

    if headers:
        headers.update(
            {k: v for k, v in headers.items() if k.lower() != "accept-encoding"}
        )

    executable = (
        shutil.which("saldl")
        or shutil.which("saldl-win64")
        or shutil.which("saldl-win32")
    )
    if not executable:
        EnvironmentError
        log.exit("Saldl executable not found...")

    arguments = [
        executable,
        # "--no-status",
        "--skip-TLS-verification",
        "--resume",
        "--merge-in-order",
        "-c8",
        "--auto-size",
        "1",
        "-D",
        str(out.parent),
        "-o",
        out.name,
    ]

    if headers:
        arguments.extend(
            ["--custom-headers", "\r\n".join([f"{k}: {v}" for k, v in headers.items()])]
        )

    # if proxy:
    #     arguments.extend(["--proxy", proxy])

    if isinstance(uri, list):
        ValueError
        log.exit(
            "Saldl code does not yet support multiple uri (e.g. segmented) downloads."
        )
    arguments.append(uri)

    try:
        subprocess.run(arguments, check=True)
    except subprocess.CalledProcessError:
        ValueError
        log.exit("Saldl failed too many times, aborting")

    log.info_("")
