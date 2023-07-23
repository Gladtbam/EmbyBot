import yaml
import json
import requests
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

nezha_url = load_config()['Probe']['URL']    
nezha_token = load_config()['Probe']['Token']
nezha_id = load_config()['Probe']['Id']

async def get_server_load():
    url = f"{nezha_url}/api/v1/server/details?id={nezha_id}"
    header = {
        'Authorization': nezha_token 
    }
    response = requests.get(url, headers=header)
    return response.json()