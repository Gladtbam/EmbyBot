from LoadConfig import init_config
import aiohttp
import asyncio
import json
import logging
import re

config = init_config()
headers = {
    # 'Content-Type': 'multipart/from-data',
    'Accept': 'application/json',
    'X-Api-Key': config.bazarr.ApiKey
    }
anime_headers = {
    'Content-Type': 'multipart/from-data',
    'Accept': 'application/json',
    'X-Api-Key': config.bazarrAnime.ApiKey
    }

async def GetSeriesEpisode(seriesInfo):
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{config.bazarr.Host}/api/episodes?seriesid%5B%5D={seriesInfo['id']}") as resp:
                if resp.status == 200:
                    data = (await resp.json()).get('data')
                    if not data:
                        return None
                    else:
                        return data
                else:
                    logging.info(f"Error getting series episode: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error getting series episode: {e}")
        return None
    
async def GetAnimeEpisode(animeInfo):
    try:
        async with aiohttp.ClientSession(headers=anime_headers) as session:
            async with session.get(f"{config.bazarrAnime.Host}/api/episodes?seriesid%5B%5D={animeInfo['id']}") as resp:
                if resp.status == 200:
                    data = (await resp.json()).get('data')
                    if not data:
                        return None
                    else:
                        return data
                else:
                    logging.info(f"Error series getting episode: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error getting series episode: {e}")
        return None
    
async def SeisesSubtitles(seriesInfo, subtitles, language):
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            data = aiohttp.FormData()
            data.add_field('file', open(subtitles, 'rb'), filename=subtitles, content_type='multipart/form-data')
            async with session.post(f"{config.bazarr.Host}/api/episodes/subtitles?seriesid={seriesInfo['sonarrSeriesId']}&episodeid={seriesInfo['sonarrEpisodeId']}&language={language}&forced=false&hi=false", data=data) as resp:
                if resp.status in [200, 204]:
                    return True
                else:
                    logging.info(f"Error uploading seises subtitles: {resp.status}")
                    return False
    except Exception as e:
        logging.error(f"Error uploading seises subtitles: {e}")
        return False
        
    
async def AnimeSubtitles(animeInfo, subtitles, language):
    try:
        async with aiohttp.ClientSession(headers=anime_headers) as session:
            data = aiohttp.FormData()
            data.add_field('file', open(subtitles, 'rb'), filename=subtitles, content_type='multipart/form-data')
            async with session.post(f"{config.bazarrAnime.Host}/api/episodes/subtitles?seriesid={animeInfo['sonarrSeriesId']}&episodeid={animeInfo['sonarrEpisodeId']}&language={language}&forced=false&hi=false", data=data) as resp:
                if resp.status in [200, 204]:
                    return True
                else:
                    logging.info(f"Error uploading anime subtitles: {resp.status}")
                    return False
    except Exception as e:
        logging.error(f"Error uploading anime subtitles: {e}")
        return False
    
async def GetMovie(movieInfo):
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{config.bazarr.Host}/api/movies?start=0&length=-1&radarrid%5B%5D={movieInfo['id']}") as resp:
                if resp.status == 200:
                    data = (await resp.json()).get('data')
                    if not data:
                        return None
                    else:
                        return data
                else:
                    logging.info(f"Error getting movie: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Error getting movie: {e}")
        return None
    
async def MoviesSubtitles(movieInfo, subtitles, language):
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            data = aiohttp.FormData()
            data.add_field('file', open(subtitles, 'rb'), filename=subtitles, content_type='multipart/form-data')
            async with session.post(f"{config.bazarr.Host}/api/movies/subtitles?radarrid={movieInfo['radarrId']}&language={language}&forced=false&hi=false", data=data) as resp:
                if resp.status in [200, 204]:
                    return True
                else:
                    logging.info(f"Error uploading movies subtitles: {resp.status}")
                    return False
    except Exception as e:
        logging.error(f"Error uploading movies subtitles: {e}")
        return False