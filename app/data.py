import yaml
import json
# from app.tgscore import user_msg_count

# 加载Config
def load_config():
    with open('config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

async def save_user_msg_count(file_path, user_msg_count):
    with open(file_path, 'w') as file:
        json.dump(user_msg_count, file)

def load_user_msg_count(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}