from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import ban_user, delete_ban, update_score
from app.emby import Ban_User, Delete_Ban
from app.tgscore import calculate_scores

scheduler = AsyncIOScheduler()

# 封禁过期用户
@scheduler.scheduled_job('cron', hour=23, minute=30)
async def ban_job():
    emby_ids = await ban_user()
    await Ban_User(emby_ids)

# 删除已封禁用户
@scheduler.scheduled_job('cron', hour=23, minute=50)
async def delete_job():
    ban_emby_ids = await delete_ban()
    await Delete_Ban(ban_emby_ids)

@scheduler.scheduled_job('cron', hour=23, minute=8)
async def score_job():
    user_ratios, total_score = await calculate_scores()
    await update_score(user_ratios, total_score)
# 启动任务
def start_scheduler():
    scheduler.start()