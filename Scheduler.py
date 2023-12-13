from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from LoadConfig import init_config
from Telegram import client
import asyncio
import threading
import logging
from ScoreManager import calculate_ratio, user_msg_count
import DataBase
import EmbyAPI

config = init_config()
scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour='0', minute='15', second='0')
async def ban_users():
    try:
        logging.info("Starting ban users job")
        embyIds = await DataBase.LimitEmbyBan()
        if embyIds is not None:
            _bool = await EmbyAPI.BanEmbyUser(embyIds)
            if _bool:
                logging.info(f"Banned {len(embyIds)} users")
            else:
                logging.error(f"Error banning users")
        else:
            logging.info("No users to ban")
    except Exception as e:
        logging.error(f"Error banning users: {e}")
    finally:
        logging.info("Ban users job finished")

@scheduler.scheduled_job('cron', hour='0', minute='30', second='0')
async def delete_ban_users():
    try:
        logging.info("Starting delete ban users job")
        embyIds = await DataBase.LimitEmbyDelete()
        if embyIds is not None:
            _bool = await EmbyAPI.DeleteBanUser(embyIds)
            if _bool:
                logging.info(f"Deleted {len(embyIds)} users")
            else:
                logging.error(f"Error deleting users")
        else:
            logging.info("No users to delete")
    except Exception as e:
        logging.error(f"Error deleting users: {e}")
    finally:
        logging.info("Delete ban users job finished")

@scheduler.scheduled_job('cron', hour='0', minute='5', second='0')
async def delete_code():
    try:
        logging.info("Starting delete code job")
        _bool = await DataBase.DeleteLimitCode()
        if _bool:
            logging.info(f"Deleted expired codes")
        else:
            logging.error(f"Error deleting code")
    except Exception as e:
        logging.error(f"Error deleting code: {e}")
    finally:
        logging.info("Delete code job finished")

@scheduler.scheduled_job('cron', hour='8,20', minute='0', second='0')
async def settle_score():
    try:
        logging.info("Starting settle score job")
        UserRatio, TotalScore = await calculate_ratio()
        userScore = await DataBase.SettleScore(UserRatio, TotalScore)
        if userScore is not None:
            message = await client.send_message(config.telegram.ChatID, f"积分结算完成, 共结算 {TotalScore} 分\n\t结算后用户积分如下:\n")
            for userId, userValue in userScore.items():
                user = await client.get_entity(userId)
                username = user.first_name + ' ' + user.last_name if user.last_name else user.first_name
                # message += f"[{username}](tg://user?id={userId}) 获得 {userValue} 分\n"
                message = await client.edit_message(message, message.text + f"\n[{username}](tg://user?id={userId}) 获得: {userValue} 积分")
            # await client.send_message(config.telegram.ChatID, message, parse_mode='Markdown')
            user_msg_count.clear()
        else:
            await client.send_message(config.telegram.ChatID, "无可结算积分")
            logging.info("No users to settle")
    except Exception as e:
        logging.error(f"Error settling score: {e}")
    finally:
        logging.info("Settle score job finished")

@scheduler.scheduled_job('cron', minute='0', second='10')
async def server_status():
    messages = None
    try:
        logging.info("Starting server status job")
        probe_info = await EmbyAPI.GetServerInfo()
        session_list = await EmbyAPI.SessionList()
        if probe_info is not None and session_list is not None:
            message = f'''
当前在线人数: {session_list}
系统负载: {probe_info['result'][0]['status']['Load5']}
CPU负载: {"{:.3f}%".format(probe_info['result'][0]['status']['CPU'])}
内存使用率: {"{:.3f}%".format((probe_info['result'][0]['status']['MemUsed'] / probe_info['result'][0]['host']['MemTotal']) * 100)}
实时下载: {"{:.2f} Mbps".format(probe_info['result'][0]['status']['NetInSpeed'] * 8 / 1_000_000)}
实时上传: {"{:.2f} Mbps".format(probe_info['result'][0]['status']['NetOutSpeed'] * 8 / 1_000_000)}

**积分注册开启, 当前注册积分**: {int(await DataBase.GetRenewValue() * config.other.Ratio)}
'''
            messages = await client.send_message(config.telegram.ChatID, message, parse_mode='Markdown')
        else:
            logging.error("Error getting server status")
    except Exception as e:
        logging.error(f"Error getting server status: {e}")
    finally:
        await asyncio.sleep(3599)
        await messages.delete() if messages is not None else None

async def start_scheduler():
    try:
        if not scheduler.running:
            scheduler.start()
            print('Press Ctrl+C to exit')
        else:
            logging.info("Scheduler already running")
    except Exception as e:
        logging.error(f"Error starting scheduler: {e}")

