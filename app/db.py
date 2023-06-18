import yaml
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


# 加载Config
def load_config():
    with open('config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

db_user = load_config()['DB_USER']
db_password = load_config()['DB_PASSWORD']
db_host = load_config()['DB_HOST']
db_port = load_config()['DB_PORT']
db_name = load_config()['DB_NAME']

# 创建数据库连接引擎
engine = create_engine(f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:3306/{db_name}')

# 创建会话工厂
Session = sessionmaker(bind=engine)

# 创建基础模型类
Base = declarative_base()

# 定义数据模型类
class User(Base):
    __tablename__ = 'users'
    tgid = Column(String(50), primary_key=True)
    embyid = Column(String(50))
    embyname = Column(String(50))
    limitdate = Column(DateTime)
    ban = Column(Boolean)
    deletedate = Column(DateTime)

class Code(Base):
    __tablename__ = 'code'
    codes = Column(String(256), primary_key=True)
    verify_key = Column(String(256))
    sha256_hash = Column(String(256))
    data = Column(String(50))

class Score(Base):
    __tablename__ = 'score'
    tgid = Column(String(50), primary_key=True)
    value = Column(Integer)

# 创建数据表（如果不存在）
Base.metadata.create_all(engine)

# 创建会话
def create_session():
    session = Session()
    return session

# 创建用户
async def create_user(tgid, embyid, embyname):
    session = create_session()

    current_time = datetime.now()
    one_month_later = current_time + timedelta(days=30)

    # 创建用户
    user = User(tgid=tgid, embyid=embyid, embyname=embyname, limitdate=one_month_later, ban=False)
    session.add(user)
    session.commit()

    session.close()

# 创建 码
async def create_code(code, public_key, sha256_hash, data):
    session = create_session()
    code = Code(codes=code, verify_key=public_key, sha256_hash=sha256_hash, data=data)
    session.add(code)
    session.commit()
    session.close()

# 搜索用户
async def search_user(tgid):
    session = create_session()
    user = session.query(User).filter(User.tgid == tgid).first()
    session.close()
    return [user.tgid, user.embyid, user.embyname, user.limitdate, user.ban, user.deletedate] if user else None     #以列表的形式返回所有

# 搜索 码
async def search_code(code):
    session = create_session()
    code_ = session.query(Code).filter(Code.codes == code).first()
    session.close()
    return [code_.codes, code_.verify_key, code_.sha256_hash, code_.data] if code_ else None

# 搜索 积分
async def search_score(tgid):
    session = create_session()
    score_ = session.query(Score).filter(Score.tgid == tgid).first()
    session.close()
    return [score_.tgid, score_.value] if score_ else None

# 删除用户(手动)
async def delete_user(tgid):
    session = create_session()
    del_user = delete(User).where(User.tgid == tgid)
    session.execute(del_user)
    session.commit()

    session.close()

# 删除 码
async def delete_code(code):
    session = create_session()
    del_code = delete(Code).where(Code.codes == code)
    session.execute(del_code)
    session.commit()
    session.close()

# 更改 积分
async def change_score(tgid, score_value):
    session = create_session()
    exist_score = session.query(Score).get(tgid)
    if exist_score:
        exist_score.value += score_value
    else:
        new_score = Score(tgid=tgid, value=score_value)
        session.add(new_score)
    session.commit()
    session.close()

# 封禁用户
async def ban_user():
    session = create_session()
    current_time = datetime.now()
    one_week_later = current_time + timedelta(days=7)

    user_ban = session.query(User).filter(User.limitdate <= current_time, User.ban == False).all()
    emby_ids = []

    for user in user_ban:
        user.ban = True
        emby_ids.append(user.embyid)                # 被封禁的用户Emby ID列表
        user.deletedate = one_week_later            # 被封禁用户待删除的时间

    session.commit()
    session.close()

    return emby_ids

# 删除已封禁用户
async def delete_ban():
    session = create_session()
    current_time = datetime.now()

    user_ban_delete = session.query(User).filter(User.deletedate <= current_time, User.ban == True).all()
    ban_emby_ids = []

    for user in user_ban_delete:
        del_user = delete(User).where(User.tgid == user.tgid)
        session.execute(del_user)
        ban_emby_ids.append(user.embyid)

    session.commit()
    session.close()
    return ban_emby_ids

# 更新 分
async def update_score(use_ratios, total_score):
    session = create_session()
    user_score = {}
    for user_id, ratio in use_ratios.items():
        score_value = int(ratio * 0.5 * total_score)
        if score_value != 0:
            exist_score = session.query(Score).get(user_id)         # 查询是否存在相同的记录

            if exist_score:
                exist_score.value += score_value
            else:
                new_score = Score(tgid=user_id, value=score_value)
                session.add(new_score)

            user_score[user_id] = score_value
    session.commit()
    session.close()

    return user_score