import requests
from datetime import datetime, timedelta
from telethon import events, Button
from telethon.tl.types import PeerChannel
from asyncio import sleep
from app.data import load_config
from app.arr.radarr import get_movie_info, add_movie
from app.arr.sonarr import get_tv_info, add_tv

api_key = load_config()['OMDB']['API_KEY']
data_info = {}
last_runtime = None

async def handle_search(client, event):
    text = event.message.text
    _, *param = text.split(' ')
    global data_info, last_runtime
    current_time = datetime.now()
    if last_runtime == None or (current_time - last_runtime >= timedelta(minutes=10)):
        if param[0] == 'tv':
            status, data_info = await get_tv_info(param[1])
        elif param[0] == 'movie':
            status, data_info = await get_movie_info(param[1])
        else:
            status = '404'
            data_info = []

        await send_info(client, event, param, status)
    else:
        await event.reply(f'上次执行时间: {last_runtime}, 请等待 10 分钟后执行')

async def get_country(name):
    imdbId = name['imdbId']
    url = f'https://www.omdbapi.com/?i={imdbId}&plot=full&apikey={api_key}'
    response = requests.get(url)

    country = response.json().get('Country', '').split(', ')[0]
    if country in ['Albania', 'Andorra', 'Anguilla', 'Antigua and Barbuda', 'Aruba', 'Austria', 'Bahamas', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Bermuda', 'Bosnia and Herzegovina', 'Bulgaria', 'Canada', 'Cayman Islands', 'Costa Rica', 'Croatia', 'Cuba', 'Czech Republic', 'Denmark', 'Dominica', 'Dominican Republic', 'El Salvador', 'Estonia', 'Faroe Islands', 'Finland', 'France', 'Germany', 'Gibraltar', 'Greece', 'Greenland', 'Grenada', 'Guadeloupe', 'Guatemala', 'Haiti', 'Vatican City', 'Honduras', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Jamaica', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Martinique', 'Mexico', 'Moldova', 'Monaco', 'Montenegro', 'Montserrat', 'Netherlands', 'Nicaragua', 'North Macedonia', 'Norway', 'Panama', 'Poland', 'Portugal', 'Romania', 'Russia', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'Trinidad and Tobago', 'Turkey', 'Turks and Caicos Islands', 'Ukraine', 'United Kingdom', 'United States', 'British Virgin Islands', 'U.S. Virgin Islands', 'Puerto Rico', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines']:
        category = '欧美'
    elif country in ['China', 'Honk Kong', 'Hong Kong Special Administrative Region', 'Macao', 'Macao Special Administrative Region', 'Taiwan']:
        category = '国产'
    elif country in ['Japan', 'North Korea', 'South Korea', 'Vietnam', 'Korea']:
        category = '日韩'
    else:
        category = '其它'
    return country, category

async def send_info(client, event, param, status):
    global data_info
    if status == '200':
        add_info = '已入库'
    elif status == '204':
        add_info = '请选择正确的分区, 点击后添加入库'
    else:
        await event.reply('未找到')

    if status in ['200', '204']:
        title = data_info['title']
        year = data_info['year']
        images = data_info['images']
        overview = data_info['overview']
        imdbId = data_info['imdbId']
        imdb_url = f'https://www.imdb.com/title/{imdbId}'

        if param[0] == 'tv':
            tvdbId = data_info['tvdbId']
            db_name = 'TVDB'
            db_url = f'http://www.thetvdb.com/?tab=series&id={tvdbId}'
        elif param[0] == 'movie':
            tmdbId = data_info['tmdbId']
            db_name = 'TMDB'
            db_url = f'https://www.themoviedb.org/movie/{tmdbId}'

        poster_url = None
        for image in images:
            if image['coverType'] == 'poster':
                if 'remoteUrl' in image:
                    poster_url = image['remoteUrl']
                else:
                    poster_url = image['url']
                break

        country, category = await get_country(data_info)

        message = f"<b>{title}</b> ({year})\n\n"
        message += f"<b>原产国：</b>{country}\n(非动画)推荐分区：{category}\n\n"
        message += f"<b>简介：</b>\n{overview}\n\n"
        buttons_movie = [
            [
                Button.inline('国产(含港澳台)', b"movie_zh"),
                Button.inline('欧美', b"movie_euus"),
                Button.inline('日韩', b"movie_jak")
            ],
            [
                Button.inline('其它', b"movie_other"),
                Button.inline('动画', b"movie_anime")
            ]
        ]
        buttons_tv = [
            [
                Button.inline('国产(含港澳台)', b"tv_zh"),
                Button.inline('欧美', b"tv_euus"),
                Button.inline('日韩', b"tv_jak")
            ],
            [
                Button.inline('其它', b"tv_other"),
                Button.inline('动画', b"tv_anime")
            ]
        ]
        buttons = [
            [
                Button.url(f'{db_name}', url=db_url),
                Button.url('IMDb', url=imdb_url)
            ],
            [
                Button.inline(f'{add_info}', data=None)
            ]
        ]
        if status == '204':
            if param[0] == 'tv':
                buttons.extend(buttons_tv)
            elif param[0] == 'movie':
                buttons.extend(buttons_movie)
        await client.send_message(event.chat_id, message, parse_mode='html', buttons=buttons, file=poster_url)

async def handle_add_search(client, event):
    category = event.data.decode()
    global data_info, last_runtime
    if category in ['movie_zh', 'movie_euus', 'movie_jak', 'movie_other', 'movie_anime']:
        if category == 'movie_zh':
            rootFolderPath = '/mnt/remote/Movie/China'
        elif category == 'movie_euus':
            rootFolderPath = '/mnt/remote/Movie/EA'
        elif category == 'movie_jak':
            rootFolderPath = '/mnt/remote/Movie/JK'
        elif category == 'movie_other':
            rootFolderPath = '/mnt/remote/Movie/Others'
        elif category == 'movie_anime':
            rootFolderPath = '/mnt/remote/Anime/Movie'
        status_code = await add_movie(data_info, rootFolderPath)
    elif category in ['tv_zh', 'tv_euus', 'tv_jak', 'tv_other', 'tv_anime']:
        if category == 'tv_zh':
            rootFolderPath = '/mnt/remote/TV/China'
        elif category == 'tv_euus':
            rootFolderPath = '/mnt/remote/TV/EA'
        elif category == 'tv_jak':
            rootFolderPath = '/mnt/remote/TV/JK'
        elif category == 'tv_other':
            rootFolderPath = '/mnt/remote/TV/Others'
        elif category == 'tv_anime':
            rootFolderPath = '/mnt/remote/Anime/TV'

        if category == 'tv_anime':
            status_code = await add_tv(data_info, rootFolderPath, seriesType='anime')
        else:
            status_code = await add_tv(data_info, rootFolderPath)
    if status_code in [200, 201]:
        await event.reply('添加成功')
        last_runtime = datetime.now()
        
        title = data_info['title']
        year = data_info['year']
        images = data_info['images']
        imdbId = data_info['imdbId']
        imdb_url = f'https://www.imdb.com/title/{imdbId}'
        poster_url = None
        for image in images:
            if image['coverType'] == 'poster':
                if 'remoteUrl' in image:
                    poster_url = image['remoteUrl']
                else:
                    poster_url = image['url']
                break
        requester_id = event.sender_id
        user = await client.get_entity(requester_id)
        username = user.first_name + ' ' + user.last_name if user.last_name else user.first_name

        message = f"<b>{title}</b> ({year})\n"
        message += f'<a href="{imdb_url}">IMDB</a>\n'
        message += f'<a href="tg://user?id={requester_id}">求片人: {username}</a>\n'

        channel = await client.get_input_entity(load_config()['Telegram']['requese_channel'])
        await client.send_message(channel, message, parse_mode='html', file=poster_url)
