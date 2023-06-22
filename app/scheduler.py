from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import ban_user, delete_ban, update_score
from app.emby import Ban_User, Delete_Ban
from app.tgscore import calculate_scores, user_msg_count
from app.tg import send_scores_to_group
from app.data import load_config, save_user_msg_count

group_id = load_config()['GROUP_ID']
# file_path = 'user_msg_count.json'
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
async def score_job(client_user):
    user_ratios, total_score = await calculate_scores()
    user_score = await update_score(user_ratios, total_score)
    await send_scores_to_group(client_user, group_id, user_score)
    user_msg_count.clear()                  # 清空字典
    # await save_user_msg_count(file_path, user_msg_count)

# 启动任务
def start_scheduler(client, client_user):
    scheduler.add_job(score_job, 'cron', hour=8, minute=0, args=[client_user])
    scheduler.start()