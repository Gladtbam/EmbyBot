import requests
import json
import random
import string
import aiohttp
from app.db import load_config

emby_url = load_config()['EMBY_URL']
api_key = load_config()['API_KEY']
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

async def User_Policy(embyid):
    data = {
        "IsAdministrator": False,
        "IsHidden": True,
        "IsHiddenRemotely": True,
        "IsHiddenFromUnusedDevices": False,
        "IsDisabled": False,
        "MaxParentalRating": 0,
        "BlockedTags": [],
        "IsTagBlockingModeInclusive": False,
        "IncludeTags": [],
        "EnableUserPreferenceAccess": True,
        "AccessSchedules": [],
        "BlockUnratedItems": [],
        "EnableRemoteControlOfOtherUsers": False,
        "EnableSharedDeviceControl": False,
        "EnableRemoteAccess": True,
        "EnableLiveTvManagement": False,
        "EnableLiveTvAccess": True,
        "EnableMediaPlayback": True,
        "EnableAudioPlaybackTranscoding": False,
        "EnableVideoPlaybackTranscoding": False,
        "EnablePlaybackRemuxing": False,
        "EnableContentDeletion": False,
        "EnableContentDeletionFromFolders": [],
        "EnableContentDownloading": False,
        "EnableSubtitleDownloading": False,
        "EnableSubtitleManagement": False,
        "EnableSyncTranscoding": False,
        "EnableMediaConversion": False,
        "EnabledChannels": [],
        "EnableAllChannels": True,
        "EnabledFolders": [],
        "EnableAllFolders": True,
        "InvalidLoginAttemptCount": 0,
        "EnablePublicSharing": False,
        "BlockedMediaFolders": [],
        "RemoteClientBitrateLimit": 0,
        # "AuthenticationProviderId": "string",
        "ExcludedSubFolders": [],
        "SimultaneousStreamLimit": 3,
        "EnabledDevices": [],
        "EnableAllDevices": True
    }
    url = f"{emby_url}/emby/Users/{embyid}/Policy"
    data = json.dumps(data)
    requests.post(url, json=data, headers=headers)

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