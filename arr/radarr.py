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
    'X-Api-Key': config.radarr.ApiKey
    }

async def movieLookup(tmdbId):
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{config.radarr.Host}/api/v3/movie/lookup/tmdb?tmdbId={tmdbId}") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.info(f"Error looking up movie: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error looking up movie: {e}")
        return None
    
async def GetMovieInfo(tmdbId):
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{config.radarr.Host}/api/v3/movie?tmdbId={tmdbId}") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.info(f"Error looking up movie: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error looking up movie: {e}")
        return None
    
async def AddMovie(movieInfo, rootFolderPath):
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(f"{config.radarr.Host}/api/v3/movie", json={
                "title": movieInfo['title'],
                "tmdbId": movieInfo['tmdbId'],
                "year": movieInfo['year'],
                "qualityProfileId": 1,
                "titleSlug": movieInfo['titleSlug'],
                "rootFolderPath": rootFolderPath,
                "monitored": True,
                "minimumAvailability": "released",
                "addOptions": {
                    "searchForMovie": True
                }
            }) as resp:
                if resp.status == 201:
                    return await resp.json()
                else:
                    logging.info(f"Error adding movie: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error adding movie: {e}")
        return None