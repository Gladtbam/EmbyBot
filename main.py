from LoadConfig import init_config
from Telegram import client
from arr import *
from notify import *
import asyncio
import threading
import DataBase
import EmbyAccount
import EmbyAPI
import GenCode
import Scheduler
import ScoreManager
import logging


if __name__ == '__main__':
    config = init_config()
    loop = asyncio.get_event_loop()
    tasks = [Scheduler.start_scheduler(), DataBase.init_db(), Notifyarr.run_webhook()]
    loop.run_until_complete(asyncio.gather(*tasks))
    client.run_until_disconnected()
