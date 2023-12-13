from . import bazarr, sonarr, radarr
import logging
import asyncio
import aiohttp
from Telegram import client
from LoadConfig import init_config
from telethon import events, types, Button
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from datetime import datetime, timedelta
import traceback
import os
import zipfile

config = init_config()

@client.on(events.CallbackQuery(data='subtitle'))
async def request_subtitle(event):
    keyboard = [
        Button.inline('电影', data='movie_subtitle'),
        Button.inline('剧集', data='series_subtitle'),
        Button.inline('动画', data='anime_subtitle'),
    ]
    message = None
    try:
        message = await event.respond('请选择上传类型', buttons=keyboard)
    except Exception as e:
        logging.error(traceback.format_exc())
    finally:
        await asyncio.sleep(10)
        await event.delete()
        await message.delete() if message is not None else None
        raise events.StopPropagation

@client.on(events.CallbackQuery(pattern=r'.*_subtitle$'))
async def subtitle(event):
    try:
        _calss = event.data.decode().split('_')[0]
        async with client.conversation(event.chat_id, timeout=60) as conv:
            await conv.send_message('请按 wiki 操作将字幕压缩成 zip 文件后发送。')
            try:
                reply_message = await conv.get_response()
                if reply_message and reply_message.file:
                    if reply_message.file.name.endswith('.zip'):
                        file_path = await reply_message.download_media(file='/tmp')
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            dbId = file_path.split('/')[-1].split('.')[0]
                            # subtitle_names = zip_ref.namelist()
                            subtitle_names = [name for name in zip_ref.namelist() if not name.endswith('/')]
                            zip_ref.extractall(path='/tmp')
                        os.remove(file_path)
                        await analyse_subtitle(_calss, dbId, subtitle_names, event)
                    else:
                        await conv.send_message('请发送一个 zip 文件')
                else:
                    await conv.send_message('请发送一个文件')
            except asyncio.TimeoutError:
                await conv.send_message('超时未收到文件')
    except asyncio.TimeoutError:
        await event.respond('超时未收到文件')
    except Exception as e:
        logging.error(traceback.format_exc())
        await event.respond('处理文件时发生错误')

async def analyse_subtitle(_calss, dbId, subtitle_names, event):
    try:
        if _calss == 'movie':
            Info = await radarr.GetMovieInfo(dbId)
        elif _calss == 'series':
            Info = await sonarr.GetSeriesInfo(dbId)
        elif _calss == 'anime':
            Info = await sonarr.GetAnimeInfo(dbId)
        else:
            Info = None
            await event.respond('未知的类型')
            
        if Info is not None and Info:
            message = await client.send_message(event.sender_id,'正在处理字幕文件...')
            if _calss == 'movie':
                movieInfo = await bazarr.GetMovie(Info)
                if movieInfo is not None and movieInfo:
                    for subtitle_name in subtitle_names:
                        subtitle = f'/tmp/{subtitle_name}'
                        language = subtitle_name[subtitle_name.index('.')+1:subtitle_name.rindex('.')]
                        _bool = await bazarr.MoviesSubtitles(movieInfo, subtitle, language)
                        if _bool:
                            await client.edit_message(message, message.text + f'\n{subtitle_name} ...... ok')
                        else:
                            await client.edit_message(message, message.text + f'\n{subtitle_name} ...... fail')
                else:
                    await client.edit_message(message, message.text + '\n未找到对应的电影')
            elif _calss == 'series':
                seriesInfo = await bazarr.GetSeriesEpisode(Info[0])
                if seriesInfo is not None and seriesInfo:
                    for subtitle_name in subtitle_names:
                        subtitle = f'/tmp/{subtitle_name}'
                        season = int(subtitle_name[subtitle_name.index('S')+1:subtitle_name.index('E')])
                        episode = int(subtitle_name[subtitle_name.index('E')+1:subtitle_name.index('.')])
                        language = subtitle_name[subtitle_name.index('.')+1:subtitle_name.rindex('.')]
                        for item in seriesInfo:
                            if item['season'] == season and item['episode'] == episode:
                                _bool = await bazarr.SeisesSubtitles(item, subtitle, language)
                                if _bool:
                                    message = await client.edit_message(message, message.text + f'\n{subtitle_name} ...... ok')
                                else:
                                    message = await client.edit_message(message, message.text + f'\n{subtitle_name} ...... fail0')
                                break
                            # else:
                                # message = await client.edit_message(message, f'{subtitle_name} ...... fail1')
                else:
                    await client.edit_message(message, message.text + '\n未找到对应的剧集')
            elif _calss == 'anime':
                animeInfo = await bazarr.GetAnimeEpisode(Info[0])
                if animeInfo is not None and animeInfo:
                    for subtitle_name in subtitle_names:
                        subtitle = f'/tmp/{subtitle_name}'
                        season = int(subtitle_name[subtitle_name.index('S')+1:subtitle_name.index('E')])
                        episode = int(subtitle_name[subtitle_name.index('E')+1:subtitle_name.index('.')])
                        language = subtitle_name[subtitle_name.index('.')+1:subtitle_name.rindex('.')]
                        for item in animeInfo:
                            if item['season'] == season and item['episode'] == episode:
                                _bool = await bazarr.AnimeSubtitles(item, subtitle, language)
                                if _bool:
                                    message = await client.edit_message(message, message.text + f'\n{subtitle_name} ...... ok')
                                else:
                                    message = await client.edit_message(message, message.text + f'\n{subtitle_name} ...... fail')
                                break
                            else:
                                message = await client.edit_message(message, message.text + f'\n{subtitle_name} ...... fail')
                else:
                    await client.edit_message(message, message.text + '\n未找到对应的动漫')
            else:
                await client.edit_message(message, message.text + '\n未知的类型')
        else:
            await event.respond('未找到对应的电影/剧集/动漫')
    except Exception as e:
        logging.error(traceback.format_exc())
        await event.respond('处理字幕文件时发生错误, 请检查文件名是否正确')
    finally:
        try:
            for subtitle_name in subtitle_names:
                os.remove('/tmp' + subtitle_name)
        except Exception as e:
            logging.error(f"Error deleting file: {e}")
        await asyncio.sleep(10)
        await event.delete()
        # raise events.StopPropagation
        