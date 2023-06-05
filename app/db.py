import yaml
import datetime
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
    limitdata = Column(DateTime)
    ban = Column(Boolean)

# 创建数据表（如果不存在）
Base.metadata.create_all(engine)

# 创建会话
def create_session():
    session = Session()
    return session

# 创建用户
async def create_user(tgid, embyid, embyname):
    session = create_session()

    current_time = datetime.datetime.now()
    one_month_later = current_time + datetime.timedelta(days=30)

    # 创建用户
    user = User(tgid=tgid, embyid=embyid, embyname=embyname, limitdata=one_month_later, ban=False)
    session.add(user)
    session.commit()

    session.close()

# 搜索用户
async def search_user(tgid):
    session = create_session()

    user = session.query(User).filter(User.tgid == tgid).first()
    session.close()
    return [user.tgid,user.embyid,user.embyname,user.limitdata,user.ban] if user else None     #以列表的形式返回所有

async def delete_user(tgid):
    session = create_session()

    del_user = delete(User).where(User.tgid == tgid)
    session.execute(del_user)
    session.commit()

    session.close()
