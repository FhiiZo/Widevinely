import requests
import re

from tmdbv3api import *
from widevinely import config
from widevinely.utils import logger

config = config.config

TMDb = TMDb()
if config:
    TMDb.language = config.TheMovieDB["language"]
    TMDb.api_key = config.TheMovieDB["api_key"]

log = logger.getLogger("TMDb")


def info(type_, content_name=None, content_year=None, imdb_id=None, cast=None):
    if imdb_id:
        title, tmdb_id, external_ids = search_with_id(imdb_id, type_)

    if not imdb_id or not tmdb_id:
        title, tmdb_id, external_ids = search_without_id(
            content_name, content_year, cast, type_
        )

    name = title.get("name") or title.get("title") or content_name
    year = (
        title.get("release_date")
        or title.get("first_air_date")
        or str(content_year if content_year else 0)
    )

    # Removing year from name and make sure
    # it won't have any whitespace at the end
    name = re.sub((f"{year[:4]}" if year else "0000"), "", name).rstrip()

    if not name.isascii() and TMDb.language != "en":
        TMDb.language = "en"
        return info(type_, content_name, content_year, imdb_id, cast)

    return {
        "name": name,
        "year": year,
        "synopsis": title.get("overview") or None,
        "original_language": title.get("original_language") or None,
        "tmdb_id": tmdb_id,
        "imdb_id": external_ids.get("imdb_id") or None,
        "tvdb_id": external_ids.get("tvdb_id") or None,
        "thumbnail": f"https://www.themoviedb.org/t/p/original{title['poster_path']}"
        if title.get("poster_path")
        else None,
    }


def get_title(tmdb_id, type_):
    title = requests.get(
        url=f"http://api.themoviedb.org/3/{type_}/{tmdb_id}",
        params={
            "api_key": TMDb.api_key,
            "language": TMDb.language,
            "append_to_response": "external_ids",
        },
    ).json()
    return title, tmdb_id, title.get("external_ids") or {}


def search_with_id(imdb_id, type_):
    try:
        tmdb_id = requests.get(
            url=f"http://api.themoviedb.org/3/find/{imdb_id}",
            params={"api_key": TMDb.api_key, "external_source": "imdb_id"},
        ).json()[f"{type_}_results"][0]["id"]
    except (KeyError, IndexError):
        return None, None, None

    title = requests.get(
        url=f"http://api.themoviedb.org/3/{type_}/{tmdb_id}",
        params={
            "api_key": TMDb.api_key,
            "language": TMDb.language,
            "append_to_response": "external_ids,content_ratings",
        },
    ).json()

    if imdb_id != title["external_ids"]["imdb_id"]:
        log.exit(" x The IMDb id from TMDb is different than the one provided")

    return title, tmdb_id, title["external_ids"]


def search_without_id(content_name, content_year, cast, type_, titles=[]):
    tmdb_results = (
        Movie().search(
            f"{content_name} ({content_year})" if content_year else content_name
        )
        if type_ == "movie"
        else TV().search(content_name)
    )

    if not tmdb_results and type_ == "movie":
        tmdb_results = Movie().search(content_name)

    if len(tmdb_results) == 1:
        if str(content_year) not in getattr(
            tmdb_results[0], "release_date", "0000"
        ) or str(content_year) not in getattr(
            tmdb_results[0], "first_air_date", "0000"
        ):
            tmdb_results = (
                Movie().search(content_name)
                if type_ == "movie"
                else TV().search(content_name)
            )

    if len(tmdb_results) == 1:
        return get_title(tmdb_results[0].id, type_)

    if content_year:
        titles = [
            x
            for x in tmdb_results
            if str(content_year) in getattr(x, "release_date", "0000")
            or str(content_year) in getattr(x, "first_air_date", "0000")
        ]

        if not titles:
            years = []
            for x in tmdb_results:
                if "release_date" in x and x.release_date:
                    if not any(title == int(x.release_date[:4]) for title in titles):
                        years.append(int(x.release_date[:4]))
                elif "first_air_date" in x and x.first_air_date:
                    if not any(title == int(x.first_air_date[:4]) for title in titles):
                        years.append(int(x.first_air_date[:4]))

            if years:
                closest_year = min(years, key=lambda x: abs(int(x) - int(content_year)))
                titles = [
                    next(
                        x
                        for x in tmdb_results
                        if getattr(x, "release_date", None)
                        and int(x.release_date[:4]) == closest_year
                        or getattr(x, "first_air_date", None)
                        and int(x.first_air_date[:4]) == closest_year
                    )
                ]

    if not titles:
        titles = tmdb_results

    if titles:
        for title in titles if len(titles) != 1 else [titles[0]]:
            credits = requests.get(
                url=f"http://api.themoviedb.org/3/{type_}/{title.id}/credits",
                params={"api_key": TMDb.api_key},
            ).json()["cast"]
            if cast and credits:
                credit_matches = list(
                    set(cast).intersection(set([x["name"] for x in credits]))
                )
                if len(credit_matches) > 2:
                    return get_title(title.id, type_)

    return {}, 0, {}
