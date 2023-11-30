from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from LoadConfig import load_config
import logging

config = load_config()

engine = create_engine(f'mysql+mysqlconnector://{config.dataBase.User}:{config.dataBase.Password}@{config.dataBase.Host}:{config.dataBase.Port}/{config.dataBase.Database}')
Session = sessionmaker(bind=engine)

Base = declarative_base()
class User(Base):
    __tablename__ = 'Users'
    TelegramId = Column(Integer, primary_key=True)
    Score = Column(Integer)
    Checkin = Column(Integer)
    Warning = Column(Integer)
    LastCheckin = Column(DateTime)

class Emby(Base):
    __tablename__ = 'Emby'
    TelegramId = Column(Integer, ForeignKey('Users.TelegramId'), primary_key=True)
    EmbyId = Column(String)
    EmbyName = Column(String)
    LimitDate = Column(DateTime)
    Ban = Column(Boolean)
    deleteDate = Column(DateTime)

class Code(Base):
    __tablename__ = 'Codes'
    CodeId = Column(String, primary_key=True)
    TimeStamp = Column(String)

Base.metadata.create_all(engine)

async def CreateUser(TelegramId):
    try:
        session = Session()
        user = session.query(User).get(TelegramId)
        if user is None:
            session.add(User(TelegramId=TelegramId, Score=0, Checkin=0, Warning=0, LastCheckin=datetime.now()))
            session.commit()
            session.close()
            logging.info(f'User {TelegramId} created successfully.')
            return True
        else:
            logging.error(f'User {TelegramId} already exists.')
            session.close()
            return False
    except Exception as e:
        logging.error(f'Error occurred while creating user {TelegramId}: {e}')
        return False
async def DeleteUser(TelegramId):
    try:
        session = Session()
        session.query(User).filter(User.TelegramId == TelegramId).delete()
        session.commit()
        session.close()
        logging.info(f'User {TelegramId} deleted successfully.')
        return True
    except Exception as e:
        logging.error(f'Error occurred while deleting user {TelegramId}: {e}')
        return False
async def GetUser(TelegramId):
    try:
        session = Session()
        user = session.query(User).get(TelegramId)
        session.close()
        return user
    except Exception as e:
        logging.error(f'Error occurred while getting user {TelegramId}: {e}')
        return None
async def ChangeUserScore(TelegramId, Score):
    try:
        session = Session()
        user = session.query(User).get(TelegramId)
        if user is not None:
            user.Score += Score
            session.commit()
            session.close()
            logging.info(f'User {TelegramId} score changed successfully.')
            return True
        else:
            logging.error(f'User {TelegramId} not found.')
            return False
    except Exception as e:
        logging.error(f'Error occurred while changing user {TelegramId} score: {e}')
        return False
async def ChangeUserCheckin(TelegramId):
    try:
        session = Session()
        user = session.query(User).get(TelegramId)
        if user is not None:
            user.Checkin += 1 # type: ignore
            user.LastCheckin = datetime.now().date() # type: ignore
            session.commit()
            session.close()
            logging.info(f'User {TelegramId} checkin changed successfully.')
            return True
        else:
            logging.error(f'User {TelegramId} not found.')
            return False
    except Exception as e:
        logging.error(f'Error occurred while changing user {TelegramId} checkin: {e}')
        return False
async def ChangeUserWarning(TelegramId, Warning=1):
    try:
        session = Session()
        user = session.query(User).get(TelegramId)
        if user is not None:
            user.Warning += Warning # type: ignore
            session.commit()
            session.close()
            logging.info(f'User {TelegramId} warning changed successfully.')
            return True
        else:
            logging.error(f'User {TelegramId} not found.')
            return False
    except Exception as e:
        logging.error(f'Error occurred while changing user {TelegramId} warning: {e}')
        return False
    
async def CreateEmbyUser(TelegramId, EmbyId, EmbyName):
    try:
        if TelegramId in config.other.AdminId:
            LimitDate = datetime.now().date() + timedelta(weeks=4752)
        else:
            LimitDate = datetime.now().date() + timedelta(days=30)
        session = Session()
        session.add(Emby(TelegramId=TelegramId, EmbyId=EmbyId, EmbyName=EmbyName, LimitDate=LimitDate, Ban=False))
        session.commit()
        session.close()
        logging.info(f'Emby user {EmbyId} created successfully.')
        return True
    except Exception as e:
        logging.error(f'Error occurred while creating Emby user {EmbyId}: {e}')
        return False
async def DeleteEmbyUser(TelegramId):
    try:
        session = Session()
        user = session.query(Emby).filter(Emby.TelegramId == TelegramId).delete()
        session.commit()
        session.close()
        logging.info(f'Emby user {TelegramId} deleted successfully.')
        return user
    except Exception as e:
        logging.error(f'Error occurred while deleting Emby user {TelegramId}: {e}')
        return None
async def GetEmbyUser(TelegramId):
    try:
        session = Session()
        emby = session.query(Emby).filter(Emby.TelegramId == TelegramId).first()
        session.close()
        return emby
    except Exception as e:
        logging.error(f'Error occurred while getting Emby user {TelegramId}: {e}')
        return None
async def BanEmbyUser():
    try:
        seesion = Session()
        users = seesion.query(Emby).filter(Emby.LimitDate < datetime.now().date(), Emby.Ban == False).all()
        embyIds = []
        for user in users:
            user.Ban = True # type: ignore
            embyIds.append(user.EmbyId)
            user.deleteDate = datetime.now().date() + timedelta(days=7) # type: ignore
        seesion.commit()
        seesion.close()
        logging.info(f'Emby users {embyIds} banned successfully.')
        return embyIds
    except Exception as e:
        logging.error(f'Error occurred while banning Emby users: {e}')
        return None
async def DeleteBanEmbyUser():
    try:
        seesion = Session()
        users = seesion.query(Emby).filter(Emby.deleteDate < datetime.now().date(), Emby.Ban == True).all()
        embyIds = []
        for user in users:
            embyIds.append(user.EmbyId)
            seesion.query(Emby).filter(Emby.TelegramId == user.TelegramId).delete()
        seesion.commit()
        seesion.close()
        logging.info(f'Emby users {embyIds} deleted successfully.')
        return embyIds
    except Exception as e:
        logging.error(f'Error occurred while deleting Emby users: {e}')
        return None
async def UpdateLimitDate(TelegramId, days=30):
    try:
        session = Session()
        user = session.query(Emby).filter(Emby.TelegramId == TelegramId).first()
        if user is not None:
            user.LimitDate = datetime.now().date() + timedelta(days=days) # type: ignore
            user.Ban = False # type: ignore
            session.commit()
            session.close()
            logging.info(f'Emby user {TelegramId} LimitDate changed successfully.')
            return True
        else:
            logging.error(f'Emby user {TelegramId} not found.')
            return False
    except Exception as e:
        logging.error(f'Error occurred while changing Emby user {TelegramId} LimitDate: {e}')
        return False
async def CreateCode(CodeId, TimeStamp):
    try:
        session = Session()
        session.add(Code(CodeId=CodeId, TimeStamp=TimeStamp))
        session.commit()
        session.close()
        logging.info(f'Code {CodeId} created successfully.')
        return True
    except Exception as e:
        logging.error(f'Error occurred while creating code {CodeId}: {e}')
        return False
async def GetCode(CodeId):
    try:
        session = Session()
        code = session.query(Code).filter(Code.CodeId == CodeId).first()
        session.close()
        return code
    except Exception as e:
        logging.error(f'Error occurred while getting code {CodeId}: {e}')
        return None
async def DeleteCode(CodeId):
    try:
        session = Session()
        session.query(Code).filter(Code.CodeId == CodeId).delete()
        session.commit()
        session.close()
        logging.info(f'Code {CodeId} deleted successfully.')
        return True
    except Exception as e:
        logging.error(f'Error occurred while deleting code {CodeId}: {e}')
        return False
async def DeleteLimitCode():
    try:
        session = Session()
        session.query(Code).filter(Code.TimeStamp < (datetime.now() - timedelta(days=90)).timestamp()).delete()
        session.commit()
        session.close()
        logging.info(f'Limit code deleted successfully.')
        return True
    except Exception as e:
        logging.error(f'Error occurred while deleting limit code: {e}')
        return False
    
async def SettleUserScore(UserRatio, TotalScore):
    try:
        session = Session()
        userScore = {}
        for userId, ratio in UserRatio.items():
            userValue = int(TotalScore * ratio * 0.5)
            if userValue < 1:
                userValue = 1
            user = session.query(User).filter(User.TelegramId == userId).first()
            if user is not None:
                user.Score += userValue # type: ignore
            else:
                session.add(User(TelegramId=userId, Score=userValue, Checkin=0, Warning=0, LastCheckin=datetime.now().date()))
            userScore[userId] = userValue
        session.commit()
        session.close()
        return userScore
    except Exception as e:
        logging.error(f'Error occurred while settling user score: {e}')
        return None
    
async def GetRenewValue():
    try:
        session = Session()
        average = session.query(func.avg(User.Score)).filter(User.Score > 10).scalar()
        if average < 100:
            average = 100
        return average
    except Exception as e:
        logging.error(f'Error occurred while getting renew value: {e}')
        return 100