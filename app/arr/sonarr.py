from app.data import load_config
import requests
import re

sonarr_url = load_config()['Sonarr']['URL']
api_key = load_config()['Sonarr']['API_KEY']
headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Api-Key': api_key
    }

# 剧集信息
async def get_tv_info(ids):
    web_info = await tv_lookup(ids)
    if web_info:
        tvdbId = web_info[0]['tvdbId']
        local_info = await get_tv(tvdbId)
        if local_info:
            status = '200'
            tv_info = local_info
        else:
            status = '204'
            tv_info = web_info
    else:
        status = '404'
        tv_info = []
    # 列表转字典 [{}] --> {}
    if isinstance(tv_info, list) and len(tv_info) > 0 and isinstance(tv_info[0], dict):
        tv_info = tv_info[0]
    else:
        tv_info = tv_info
    return status, tv_info

# 搜索剧集
async def tv_lookup(ids):
    if re.match(r'^tt\d{5,9}$', ids):                                  # imdb id
        term = f"imdb%3A{ids}"
    else: # re.match(r'^\d{5,7}$', ids):                                    # tvdb id
        term = f"tvdb%3A{ids}"
    url = f"{sonarr_url}/api/v3/series/lookup?term={term}"
    response = requests.get(url, headers=headers)
    data = response.json()
    if ('status' in data and data['status'] == 400) or ('message' in data and 'description' in data):
        data = []
    return data

# 搜索剧集(本地)
async def get_tv(tvdbId):
    url = f"{sonarr_url}/api/v3/series?tvdbId={tvdbId}"
    response = requests.get(url, headers=headers)
    if response.status_code != 400:
        data =response.json()
    else:
        data = []
    return data

# 添加剧集
async def add_tv(tv, rootFolderPath, seriesType='standard'):
    url = f"{sonarr_url}/api/v3/series"
    data = {
        "tvdbId": tv['tvdbId'],
        "monitored": True,
        "qualityProfileId": 1,
        "seasons": tv['seasons'],
        "addOptions": {
            "ignoreEpisodesWithFiles": True,
            "ignoreEpisodesWithoutFiles": False,
            "monitor": "all",
            "searchForMissingEpisodes": True,
        },
        "rootFolderPath": rootFolderPath,
        "seasonFolder": True,
        "seriesType": seriesType,
        "title": tv['title']
    }
    response = requests.post(url, json=data, headers=headers)
    return response.status_code             # 失败为400

