from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import load_config ,ban_user, delete_ban, update_score
from app.emby import Ban_User, Delete_Ban
from app.tgscore import calculate_scores, user_msg_count
from app.tg import send_scores_to_group

group_id = load_config()['GROUP_ID']
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

# @scheduler.scheduled_job('cron', hour=8, minute=0)
async def score_job(client):
    user_ratios, total_score = await calculate_scores()
    user_score = await update_score(user_ratios, total_score)
    # await send_scores_to_group(client, group_id, user_score)
    user_msg_count.clear()                  # 清空字典
# 启动任务
def start_scheduler(client):
    scheduler.add_job(score_job, 'cron', hour=8, minute=0, args=[client])
    scheduler.start()