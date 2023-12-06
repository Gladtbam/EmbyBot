from LoadConfig import init_config
from Telegram import client
import asyncio
import threading
import ScoreManager
import DataBase

if __name__ == '__main__':
    config = init_config()
    threading.Thread(target=DataBase.run_init_db).start()
    client.run_until_disconnected()