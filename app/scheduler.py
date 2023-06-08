from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import ban_user
from app.emby import Ban_User

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=0, minute=0)
async def ban_job():
    emby_ids = await ban_user()
    print(emby_ids)
    await Ban_User(emby_ids)

# 启动任务
def start_scheduler():
    scheduler.start()