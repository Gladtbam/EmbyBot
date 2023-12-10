from . import sonarr, radarr
import logging
import asyncio
import aiohttp
from Telegram import client
from LoadConfig import init_config
from telethon import events, types, Button
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from datetime import datetime, timedelta
import traceback
import io

config = init_config()
last_runtime = None
metadataInfo = {'type': None, 'info': None}

@client.on(events.NewMessage(pattern=fr'^/request(?:{config.telegram.BotName})?(\s.*)?$'))
async def search(event):
    global last_runtime, metadataInfo
    _, *args = event.text.split(' ')
    if last_runtime is None or (datetime.now() - last_runtime >= timedelta(minutes=5)):
        try:
            if args[0] == 'tv':
                seriesInfo = await sonarr.GetSeriesInfo(args[1])
                if seriesInfo is None or not seriesInfo:
                    seriesInfo = await sonarr.seriesLookup(args[1])
                    if seriesInfo is None or not seriesInfo:
                        await event.reply(f"未找到该剧集, 请检查 tvdbId 是否正确")
                    else:
                        print(seriesInfo)
                        await SendInfo(event, seriesInfo[0], _class='tv')
                        metadataInfo = {'type': 'tv', 'info': seriesInfo[0]}
                else:
                    await event.reply(f"已在队列中, 请勿重复添加")
            elif args[0] == 'anime':
                animeInfo = await sonarr.GetAnimeInfo(args[1])
                if animeInfo is None or not animeInfo:
                    animeInfo = await sonarr.animeLookup(args[1])
                    if animeInfo is None or not animeInfo:
                        await event.reply(f"未找到该动画, 请检查 tvdbId 是否正确")
                    else:
                        await SendInfo(event, animeInfo[0], _class='anime')
                        metadataInfo = {'type': 'anime', 'info': animeInfo[0]}
                else:
                    await event.reply(f"已在队列中, 请勿重复添加")
            elif args[0] == 'movie':
                movieInfo = await radarr.GetMovieInfo(args[1])
                if movieInfo is None or not movieInfo:
                    movieInfo = await radarr.movieLookup(args[1])
                    if movieInfo is None or not movieInfo:
                        await event.reply(f"未找到该电影, 请检查 tmdbId 是否正确")
                    else:
                        print(movieInfo)
                        await SendInfo(event, movieInfo, _class='movie')
                        metadataInfo = {'type': 'movie', 'info': movieInfo}
                else:
                    await event.reply(f"已在队列中, 请勿重复添加")
            else:
                await event.reply(f"未知参数: {args[0]}, 请检查参数是否正确")
            last_runtime = datetime.now()
        except Exception as e:
            logging.error(f"Error adding movie: {e}")
            logging.error(traceback.format_exc())
            await event.reply(f"查询错误: {e}")
    else:
        delta = timedelta(minutes=5) - (datetime.now() - last_runtime)
        minutes, seconds = divmod(delta.total_seconds(), 60)
        await event.reply(f"上次执行时间: {last_runtime.strftime('%Y-%m-%d %H:%M:%S')}, 请 {int(minutes)} 分 {int(seconds)} 秒后再试")

async def GetCountry(imdbId):
    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout, headers={'Accept': '*/*'}) as session:
            async with session.get(f"https://www.omdbapi.com/?i={imdbId}&plot=full&apikey={config.other.OMDBApiKey}") as resp:
                print(resp.status)
                if resp.status == 200:
                    country =  (await resp.json()).get('Country', '').split(', ')[0]
                    image = (await resp.json()).get('Poster', '')
                    if country in ['Albania', 'Andorra', 'Anguilla', 'Antigua and Barbuda', 'Aruba', 'Austria', 'Bahamas', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Bermuda', 'Bosnia and Herzegovina', 'Bulgaria', 'Canada', 'Cayman Islands', 'Costa Rica', 'Croatia', 'Cuba', 'Czech Republic', 'Denmark', 'Dominica', 'Dominican Republic', 'El Salvador', 'Estonia', 'Faroe Islands', 'Finland', 'France', 'Germany', 'Gibraltar', 'Greece', 'Greenland', 'Grenada', 'Guadeloupe', 'Guatemala', 'Haiti', 'Vatican City', 'Honduras', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Jamaica', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Martinique', 'Mexico', 'Moldova', 'Monaco', 'Montenegro', 'Montserrat', 'Netherlands', 'Nicaragua', 'North Macedonia', 'Norway', 'Panama', 'Poland', 'Portugal', 'Romania', 'Russia', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'Trinidad and Tobago', 'Turkey', 'Turks and Caicos Islands', 'Ukraine', 'United Kingdom', 'United States', 'British Virgin Islands', 'U.S. Virgin Islands', 'Puerto Rico', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines']:
                        category = '欧美'
                    elif country in ['China', 'Honk Kong', 'Hong Kong Special Administrative Region', 'Macao', 'Macao Special Administrative Region', 'Taiwan']:
                        category = '国产'
                    elif country in ['Japan', 'North Korea', 'South Korea', 'Vietnam', 'Korea']:
                        category = '日韩'
                    else:
                        category = '其它'
                    return country, category, image
                else:
                    logging.info(f"Error looking up movie: {resp.status}")
                    return None, None, None
    except Exception as e:
        logging.error(f"Error looking up movie: {e}")
        logging.error(traceback.format_exc())
        return None, None, None
    
async def SendInfo(event, info, _class):
    try:
        print(info, _class)
        country, category, image = await GetCountry(info['imdbId'])
        print(country, category)

        message = f'''
<h1><b>{info['title']}</b> ({info['year']})<h1>\n\n
<b>国家:</b> {country}\n
<b>推荐分区:</b> {category}\n
<b>简介:</b> {info['overview']}\n
<b>类型:</b> {', '.join(info['genres'])}\n
<b>语言:</b> {info['originalLanguage']['name']}\n
<b>时长:</b> {info['runtime']}\n
<h2><a href="https://www.imdb.com/title/{info['imdbId']}">IMDB</a>\t<a href="{f"https://www.themoviedb.org/movie/{info['tmdbId']}" if _class == 'movie' else f"http://www.thetvdb.com/?tab=series&id={info['tvdbId']}"}">{"TMDB" if _class == 'movie' else "TVDB"}</a></h2>\n
'''
        
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
                Button.inline('记录片', b"tv_doc"),
                Button.inline('其它', b"tv_other")
            ]
        ]
        buttons_anime = [
            [
                Button.inline('确认', b"anime")
            ]
        ]

        if image is None:
            image = 'https://artworks.thetvdb.com/banners/images/missing/movie.jpg'
        # for i in info['images']:
        #     if i['coverType'] == 'poster':
        #         image = i['remoteUrl'] if 'remoteUrl' in i else i['url']
        #     elif i['coverType'] == 'fanart':
        #         image = i['remoteUrl'] if 'remoteUrl' in i else i['url']
        
        # async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        #     async with session.get(image) as resp:
        #         if resp.status == 200:
        #             image = io.BytesIO(await resp.read())
        #         else:
        #             image = 'https://artworks.thetvdb.com/banners/images/missing/movie.jpg'

        print(image)
        if _class == 'movie':
            await client.send_message(event.chat_id, message, buttons=buttons_movie, parse_mode='html', file=image)
        elif _class == 'tv':
            await client.send_message(event.chat_id, message, buttons=buttons_tv, parse_mode='html', file=image)
        elif _class == 'anime':
            await client.send_message(event.chat_id, message, buttons=buttons_anime, parse_mode='html', file=image)
        elif _class == 'addtrue':
            user = await client.get_entity(event.sender_id)
            username = user.first_name + ' ' + user.last_name if user.last_name else user.first_name
            message += f'\n<a herf="tg://user?id={event.sender_id}">求片人{username}</a>'
            channel = await client.get_input_entity(config.telegram.RequiredChannel)
            await client.send_message(channel, message, parse_mode='html', file=image)
        else:
            await client.send_message(event.chat_id, message , parse_mode='html', file=image)
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        logging.error(traceback.format_exc())
        await event.reply(f"发送错误: {e}")

@client.on(events.CallbackQuery(pattern=r'^(movie_|tv_|anime).*$'))
async def add_search(event):
    global metadataInfo
    try:
        category = event.data.decode()
        if category == 'anime' and metadataInfo['type'] == 'anime':
            info = await sonarr.AddSeries(metadataInfo['info'], '/mnt/remote/Anime/TV', 'anime')
        elif category == 'tv_zh' and metadataInfo['type'] == 'tv':
            info = await sonarr.AddSeries(metadataInfo['info'], '/mnt/remote/TV/China', 'standard')
        elif category == 'tv_euus' and metadataInfo['type'] == 'tv':
            info = await sonarr.AddSeries(metadataInfo['info'], '/mnt/remote/TV/EA', 'standard')
        elif category == 'tv_jak' and metadataInfo['type'] == 'tv':
            info = await sonarr.AddSeries(metadataInfo['info'], '/mnt/remote/TV/JK', 'standard')
        elif category == 'tv_doc' and metadataInfo['type'] == 'tv':
            info = await sonarr.AddSeries(metadataInfo['info'], '/mnt/remote/Documentary', 'standard')
        elif category == 'tv_other' and metadataInfo['type'] == 'tv':
            info = await sonarr.AddSeries(metadataInfo['info'], '/mnt/remote/TV/Others', 'standard')
        elif category == 'movie_zh' and metadataInfo['type'] == 'movie':
            info = await radarr.AddMovie(metadataInfo['info'], '/mnt/remote/Movie/China')
        elif category == 'movie_euus' and metadataInfo['type'] == 'movie':
            info = await radarr.AddMovie(metadataInfo['info'], '/mnt/remote/Movie/EA')
        elif category == 'movie_jak' and metadataInfo['type'] == 'movie':
            info = await radarr.AddMovie(metadataInfo['info'], '/mnt/remote/Movie/JK')
        elif category == 'movie_other' and metadataInfo['type'] == 'movie':
            info = await radarr.AddMovie(metadataInfo['info'], '/mnt/remote/Movie/Others')
        elif category == 'movie_anime' and metadataInfo['type'] == 'movie':
            info = await radarr.AddMovie(metadataInfo['info'], '/mnt/remote/Anime/Movie')
        else:
            info = None

        if info is not None:
            await event.answer(f"添加成功")
            await SendInfo(event, info, _class='addtrue')
        else:
            await event.answer(f"添加失败")
    except Exception as e:
        logging.error(f"Error adding movie: {e}")
        logging.error(traceback.format_exc())
        await event.answer(f"添加失败: {e}")