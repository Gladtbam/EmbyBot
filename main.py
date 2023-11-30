from LoadConfig import init_config
from Telegram import client
import asyncio
import ScoreManager


if __name__ == '__main__':
    config = init_config()
    client.run_until_disconnected()