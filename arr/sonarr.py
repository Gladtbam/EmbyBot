import aiohttp
import asyncio
import json
import logging
from LoadConfig import init_config
import re

config = init_config()
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Api-Key': config.sonarr.ApiKey
    }
anime_headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Api-Key': config.sonarrAnime.ApiKey
    }

async def seriesLookup(tvdbId, seriesType):
    try:
        if seriesType == "anime":
            seriesHeaders = anime_headers
            seriesHost = config.sonarrAnime.Host
        elif seriesType == "tv":
            seriesHeaders = headers
            seriesHost = config.sonarr.Host
        async with aiohttp.ClientSession(headers=seriesHeaders) as session:
            async with session.get(f"{seriesHost}/api/v3/series/lookup?term=tvdb%3A{tvdbId}") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.info(f"Error looking up series: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error looking up series: {e}")
        return None
    
# async def animeLookup(tvdbId):
#     try:
#         async with aiohttp.ClientSession(headers=anime_headers) as session:
#             async with session.get(f"{config.sonarrAnime.Host}/api/v3/series/lookup?term=tvdb%3A{tvdbId}") as resp:
#                 if resp.status == 200:
#                     return await resp.json()
#                 else:
#                     logging.info(f"Error looking up series: {resp.status}")
#                     return None
#     except Exception as e:
#         logging.error(f"Error looking up series: {e}")
#         return None
    
async def GetSeriesInfo(tvdbId, seriesType):
    try:
        if seriesType == "anime":
            seriesHeaders = anime_headers
            seriesHost = config.sonarrAnime.Host
        elif seriesType == "tv":
            seriesHeaders = headers
            seriesHost = config.sonarr.Host
        async with aiohttp.ClientSession(headers=seriesHeaders) as session:
            async with session.get(f"{seriesHost}/api/v3/series?tvdbId={tvdbId}&includeSeasonImages=true") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.info(f"Error looking up series: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error looking up series: {e}")
        return None

# async def GetAnimeInfo(tvdbId):
#     try:
#         async with aiohttp.ClientSession(headers=anime_headers) as session:
#             async with session.get(f"{config.sonarrAnime.Host}/api/v3/series?tvdbId={tvdbId}&includeSeasonImages=true") as resp:
#                 if resp.status == 200:
#                     return await resp.json()
#                 else:
#                     logging.info(f"Error looking up series: {resp.status}")
#                     return None
#     except Exception as e:
#         logging.error(f"Error looking up series: {e}")
#         return None
    
async def GetEpisodeInfo(seriesId, seriesType):
    try:
        if seriesType == "anime":
            seriesHeaders = anime_headers
            seriesHost = config.sonarrAnime.Host
        elif seriesType == "tv":
            seriesHeaders = headers
            seriesHost = config.sonarr.Host
        async with aiohttp.ClientSession(headers=seriesHeaders) as session:
            async with session.get(f"{seriesHost}/api/v3/episode?seriesId={seriesId}&includeImages=true") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.info(f"Error looking up series: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error looking up series: {e}")
        return None

async def GetEpisodeId(episodeId, seriesType):
    try:
        if seriesType == "anime":
            seriesHeaders = anime_headers
            seriesHost = config.sonarrAnime.Host
        elif seriesType == "tv":
            seriesHeaders = headers
            seriesHost = config.sonarr.Host
        async with aiohttp.ClientSession(headers=seriesHeaders) as session:
            async with session.get(f"{seriesHost}/api/v3/episode/{episodeId}") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.info(f"Error looking up series: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error looking up series: {e}")
        return None
    
async def AddSeries(seriesInfo, rootFolderPath, seriesType):
    try:
        if seriesType == "anime":
            async with aiohttp.ClientSession(headers=anime_headers) as session:
                async with session.post(f"{config.sonarrAnime.Host}/api/v3/series", json={
                    "tvdbId": seriesInfo["tvdbId"],
                    "monitored": True,
                    "qualityProfileId": 1,
                    "seasons": seriesInfo["seasons"],
                    "seasonFolder": True,
                    "rootFolderPath": rootFolderPath,
                    "seriesType": seriesType,
                    "title": seriesInfo["title"],
                    "addOptions": {
                        "ignoreEpisodesWithFiles": True,
                        "ignoreEpisodesWithoutFiles": False,
                        "searchForMissingEpisodes": True
                    }
                    }) as resp:
                    if resp.status == 201:
                        logging.info(f"Added series: {seriesInfo['tvdbId']}")
                        return await resp.json()
                    else:
                        logging.info(f"Error adding series: {resp.status}")
                        return None
        elif seriesType == "standard":
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(f"{config.sonarr.Host}/api/v3/series", json={
                    "tvdbId": seriesInfo["tvdbId"],
                    "monitored": True,
                    "qualityProfileId": 1,
                    "seasons": seriesInfo["seasons"],
                    "seasonFolder": True,
                    "rootFolderPath": rootFolderPath,
                    "seriesType": seriesType,
                    "title": seriesInfo["title"],
                    "addOptions": {
                        "ignoreEpisodesWithFiles": True,
                        "ignoreEpisodesWithoutFiles": False,
                        "searchForMissingEpisodes": True
                    }
                    }) as resp:
                    if resp.status == 201:
                        logging.info(f"Added series: {seriesInfo['tvdbId']}")
                        return await resp.json()
                    else:
                        logging.info(f"Error adding series: {resp.status}")
                        return None
    except Exception as e:
        logging.error(f"Error adding series: {e}")
        return False