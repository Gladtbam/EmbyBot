from app.data import load_config
import requests
import re

radarr_url = load_config()['Radarr']['URL']
api_key = load_config()['Radarr']['API_KEY']
headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Api-Key': api_key
    }

# 电影信息
async def get_movie_info(ids):
    web_info = await movie_lookup(ids)
    if web_info:
        tmdbId = web_info['tmdbId']
        local_info = await get_movie(tmdbId)
        if local_info:
            status = '200'
            movie_info = local_info
        else:
            status = '204'
            movie_info = web_info
    else:
        status = '404'
        movie_info = []
    # 列表转字典 [{}] --> {}
    if isinstance(movie_info, list) and len(movie_info) > 0 and isinstance(movie_info[0], dict):
        movie_info = movie_info[0]
    else:
        movie_info = movie_info
    return status, movie_info

# 搜索电影
async def movie_lookup(ids):
    if re.match(r'^tt\d{7}$', ids):                                  # imdb id
        url = f"{radarr_url}/api/v3/movie/lookup/imdb?imdbId={ids}"
    else: # re.match(r'^\d{5,7}$', ids):                                    # tmdb id
        url = f"{radarr_url}/api/v3/movie/lookup/tmdb?tmdbId={ids}"

    response = requests.get(url, headers=headers)
    data = response.json()
    if ('status' in data and data['status'] == 400) or ('message' in data and 'description' in data):
        data = []
    return data

# 搜索电影(本地)
async def get_movie(tmdbId):
    url = f"{radarr_url}/api/v3/movie?tmdbId={tmdbId}"
    response = requests.get(url, headers=headers)
    if response.status_code != 400:
        data =response.json()
    else:
        data = []
    return data

# 添加电影
async def add_movie(movie, rootFolderPath):
    url = f"{radarr_url}/api/v3/movie"
    data = {
        "tmdbId": movie['tmdbId'],
        "monitored": True,
        "qualityProfileId": 1,
        "minimumAvailability": "released",
        "addOptions": {
            "searchForMovie": True
        },
        "rootFolderPath": rootFolderPath,
        "title": movie['title']
    }
    response = requests.post(url, json=data, headers=headers)
    return response.status_code             # 失败为400

