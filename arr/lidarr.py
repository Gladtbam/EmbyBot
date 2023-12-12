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
    'X-Api-Key': config.lidarr.ApiKey
    }

async def artistLookup(musicBrainzId):
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{config.lidarr.Host}/api/v1/artist/lookup?term=mbid%3A{musicBrainzId}") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.info(f"Error looking up artist: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error looking up artist: {e}")
        return None
    
async def albumLookup(musicBrainzId):
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{config.lidarr.Host}/api/v1/album/lookup?term=mbid%3A{musicBrainzId}") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.info(f"Error looking up album: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error looking up album: {e}")
        return None