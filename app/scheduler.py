from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import ban_user, delete_ban, update_score, del_limit_code
from app.emby_api import Ban_User, Delete_Ban, session_list
from app.score_man import calculate_scores, user_msg_count
from app.score_man import send_scores_to_group
from app.data import load_config, get_server_load
from asyncio import sleep

chat_id = load_config()['GROUP_ID']
scheduler = AsyncIOScheduler()

# 封禁过期用户
@scheduler.scheduled_job('cron', hour=0, minute=15)
async def ban_job():
    emby_ids = await ban_user()
    await Ban_User(emby_ids)

# 删除已封禁用户
@scheduler.scheduled_job('cron', hour=0, minute=30)
async def delete_job():
    ban_emby_ids = await delete_ban()
    await Delete_Ban(ban_emby_ids)

# 删除过期 "码"
@scheduler.scheduled_job('cron', hour=0, minute=2)
async def code_job():
    await del_limit_code()

# @scheduler.scheduled_job('cron', hour=8, minute=0)
async def score_job(client_user):
    user_ratios, total_score = await calculate_scores()
    user_score = await update_score(user_ratios, total_score)
    await send_scores_to_group(client_user, chat_id, user_score)
    user_msg_count.clear()                  # 清空字典

# @scheduler.scheduled_job('cron', hour=8, minute=0)
async def server_load_job(client_user):
    signup_value = int(init_renew_value()) * load_config()['SIGNUP']
    _session_list = await session_list()
    server_info = await get_server_load()
    cpu_info = "{:.3f}%".format(server_info['result'][0]['status']['CPU'])
    memory_used_percent = "{:.3f}%".format((server_info['result'][0]['status']['MemUsed'] / server_info['result'][0]['host']['MemTotal']) * 100)
    # 实时上传下载速度
    net_in_speed = "{:.2f} Mbps".format(server_info['result'][0]['status']['NetInSpeed'] * 8 / 1_000_000)
    net_out_speed = "{:.2f} Mbps".format(server_info['result'][0]['status']['NetOutSpeed'] * 8 / 1_000_000)

    # 总上传下载传输量
    net_in_transfer = "{:.2f} TB".format(server_info['result'][0]['status']['NetInTransfer'] / (1024**4))
    net_out_transfer = "{:.2f} TB".format(server_info['result'][0]['status']['NetOutTransfer'] / (1024**4))

    message = f'''
服务器状态:
在线人数: {_session_list}
系统负载: {server_info['result'][0]['status']['Load5']}
CPU 负载: {cpu_info}
内存使用率: {memory_used_percent}
实时下载: {net_in_speed}
实时上传: {net_out_speed}
总下载量: {net_in_transfer}
总上传量: {net_out_transfer}
当前注册积分: {signup_value}
'''
    messages = await client_user.send_message(chat_id, message, parse_mode='Markdown')
    await sleep(1000)
    await messages.delete()

# 启动任务
async def start_scheduler(client_user):
    if not scheduler.running:
        print('Press Ctrl+C to exit')
        scheduler.add_job(score_job, 'cron', hour=8, minute=0, args=[client_user])
        scheduler.add_job(score_job, 'cron', hour=20, minute=0, args=[client_user])
        scheduler.add_job(server_load_job, 'cron',minute=0, second=10, args=[client_user])
        scheduler.start()