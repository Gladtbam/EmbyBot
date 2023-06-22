from telethon import events, types
from app.data import load_config, save_user_msg_count

group_id = load_config()['GROUP_ID']
# file_path = 'user_msg_count.json'

user_msg_count = {}

def score_commands(client):
    @client.on(events.NewMessage(chats=group_id))
    async def handle_new_message(event):                        # 统计用户消息
        if isinstance(event.message, types.Message) and isinstance(event.message.from_id, types.PeerUser):
            user_id = event.message.from_id.user_id
            message = event.message

            if message.media is not None:
                if message.photo is not None:
                    msg_type = 'photo'
                elif message.video is not None:
                    msg_type = 'video'
                elif message.document is not None:
                    msg_type = 'document'
                else:
                    msg_type = 'media'
            else:
                msg_type = 'text'
            
            if user_id in user_msg_count:
                if msg_type in user_msg_count[user_id]:
                    user_msg_count[user_id][msg_type] += 1
                else:
                    user_msg_count[user_id][msg_type] = 1
            else:
                user_msg_count[user_id] = {msg_type: 1}
            print(user_msg_count)
            # await save_user_msg_count(file_path, user_msg_count)

# 计算比例
async def calculate_scores():
    scores = {}
    total_score = 0

    for user_id, messages in user_msg_count.items():
        score = 0
        for msg_type, count in messages.items():
            if msg_type in ['photo', 'video']:            # 图片和视频消息 2分
                score += count * 2
            elif msg_type == 'text':                        # 文本消息 1分
                score += count * 1
            elif msg_type == 'voice':                       # 视频消息 3分
                score += count * 3
            elif msg_type == 'document':                    # 文件(贴纸)消息 3分
                score += count * 1
        scores[user_id] = score
        total_score += score

    user_ratios = {}
    for user_id, score in scores.items():
        ratio = score / total_score
        user_ratios[user_id] = ratio

    return user_ratios, total_score