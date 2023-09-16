import yaml
import json
import requests
import re
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

# 处理输入的时间数据
async def parse_combined_duration(duration_str):
    total_seconds = 0
    pattern = r'(\d+h)?(\d+m)?(\d+s)?'
    match = re.match(pattern, duration_str)
    if match:
        hours = match.group(1)
        minutes = match.group(2)
        seconds = match.group(3)

        if hours:
            hours = int(hours[:-1])  # 去除末尾的 'h' 并转换为整数
            total_seconds += hours * 3600

        if minutes:
            minutes = int(minutes[:-1])  # 去除末尾的 'm' 并转换为整数
            total_seconds += minutes * 60

        if seconds:
            seconds = int(seconds[:-1])  # 去除末尾的 's' 并转换为整数
            total_seconds += seconds

    return total_seconds

# 计算总时间
async def parse_duration(duration_str):
    total_seconds = 0
    pattern = r'(\d+)([hms])'
    matches = re.findall(pattern, duration_str)
    for value, unit in matches:
        value = int(value)
        if unit == 'h':
            total_seconds += value * 3600
        elif unit == 'm':
            total_seconds += value * 60
        elif unit == 's':
            total_seconds += value
    return total_seconds