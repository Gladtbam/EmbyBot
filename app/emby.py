import requests
import json
import random
import string
import aiohttp
from app.data import load_config

emby_url = load_config()['Emby']['URL']
api_key = load_config()['Emby']['API_KEY']
headers = {
        'Content-Type': 'application/json'
    }

async def New_User(tgname):
    data = {
        "Name": tgname
    }
    url = f"{emby_url}/emby/Users/New?api_key={api_key}"
    create_user = requests.post(url, json=data, headers=headers)
    embyid = create_user.json()['Id']
    return embyid

async def User_Policy(embyid, BlockMeida):
    data = {
        "IsAdministrator": False,                   # 是否为管理员
        "IsHidden": True,                           # 用户是否隐藏
        "IsHiddenRemotely": True,                   # 是否在远程访问时隐藏
        "IsHiddenFromUnusedDevices": False,         # 是否在未使用的设备上隐藏
        "IsDisabled": False,                        # 用户是否被禁用
        # "MaxParentalRating": 0,                     # 最大家长级别
        "BlockedTags": [],                          # 被阻止的标签列表
        "IsTagBlockingModeInclusive": False,        # 是否以标签阻止模式进行阻止
        "IncludeTags": [],                          # 包含的标签列表
        "EnableUserPreferenceAccess": True,         # 是否允许用户访问首选项
        "AccessSchedules": [],                      # 定义用户的访问时间
        "BlockUnratedItems": [],                    # 阻止的未评级项目列表
        "EnableRemoteControlOfOtherUsers": False,   # 是否允许远程控制其他用户
        "EnableSharedDeviceControl": False,         # 是否允许共享设备的控制
        "EnableRemoteAccess": True,                 # 是否允许远程访问
        "EnableLiveTvManagement": False,            # 是否允许管理 Live TV
        "EnableLiveTvAccess": True,                 # 是否允许访问 Live TV
        "EnableMediaPlayback": True,                # 是否允许媒体播放
        "EnableAudioPlaybackTranscoding": False,    # 表示是否允许音频转码
        "EnableVideoPlaybackTranscoding": False,    # 表示是否允许视频转码
        "EnablePlaybackRemuxing": False,            # 是否允许媒体复用
        "EnableContentDeletion": False,             # 是否允许删除内容
        "EnableContentDeletionFromFolders": [],     # 允许从指定文件夹删除内容
        "EnableContentDownloading": False,          # 是否允许下载内容
        "EnableSubtitleDownloading": False,         # 是否允许下载字幕
        "EnableSubtitleManagement": False,          # 是否允许管理字幕
        "EnableSyncTranscoding": False,             # 是否允许同步转码
        "EnableMediaConversion": False,             # 是否允许媒体转换
        "EnabledChannels": [],                      # 允许访问的频道列表
        "EnableAllChannels": True,                  # 是否允许访问所有频道
        "EnabledFolders": [],                       # 允许访问的文件夹列表
        "EnableAllFolders": True,                   # 是否允许访问所有文件夹
        "InvalidLoginAttemptCount": 0,              # 无效登录尝试的次数
        "EnablePublicSharing": False,               # 是否允许公开共享
        "BlockedMediaFolders": [BlockMeida],                  # 被阻止的媒体文件夹列表
        "RemoteClientBitrateLimit": 0,              # 远程客户端的比特率限制
        # "AuthenticationProviderId": "string",     # 认证提供者的 ID
        "ExcludedSubFolders": [],                   # 排除的子文件夹列表
        "SimultaneousStreamLimit": 3,               # 同时流式传输的限制
        "EnabledDevices": [],                       # 允许访问的设备列表
        "EnableAllDevices": True                    # 是否允许访问所有设备
    }
    url = f"{emby_url}/emby/Users/{embyid}/Policy?api_key={api_key}"
    requests.post(url, json=data, headers=headers)

async def Get_UserInfo(embyid):
    url = f"{emby_url}/emby/Users/{embyid}?api_key={api_key}"
    response = requests.get(url, headers=headers)
    user_info = response.json()
    return user_info

async def Password(embyid):
    Pw = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(12))
    data = {
        "Id": embyid,
        "CurrentPw": "",
        "NewPw": Pw,
        "ResetPassword": False
    }
    url = f"{emby_url}/emby/Users/{embyid}/Password?api_key={api_key}"
    requests.post(url, json=data, headers=headers)
    return Pw

async def User_delete(embyid):
    url = f"{emby_url}/emby/Users/{embyid}?api_key={api_key}"
    requests.delete(url, headers=headers)

async def Ban_User(emby_ids):
    for embyid in emby_ids:
        data = {
            "IsDisabled": True
        }
        url = f"{emby_url}/emby/Users/{embyid}/Policy?api_key={api_key}"
        requests.post(url, json=data, headers=headers)

# 删除已封禁用户
async def Delete_Ban(ban_emby_ids):
    for embyid in ban_emby_ids:
        url = f"{emby_url}/emby/Users/{embyid}?api_key={api_key}"
        requests.delete(url, headers=headers)
