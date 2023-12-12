from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, select, delete, update, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from LoadConfig import init_config
import logging
import asyncio

config = init_config()

engine = create_async_engine(f'mysql+asyncmy://{config.dataBase.User}:{config.dataBase.Password}@{config.dataBase.Host}:{config.dataBase.Port}/{config.dataBase.DatabaseName}')

Base = declarative_base()
class User(Base):
    __tablename__ = 'Users'
    TelegramId = Column(String(20), primary_key=True)
    Score = Column(Integer, default=0)
    Checkin = Column(Integer, default=0)
    Warning = Column(Integer, default=0)
    LastCheckin = Column(DateTime, default=datetime.now().date())
    def __repr__(self):
        return f'<User(TelegramId={self.TelegramId}, Score={self.Score}, Checkin={self.Checkin}, Warning={self.Warning}, LastCheckin={self.LastCheckin})>'
    
class Emby(Base):
    __tablename__ = 'Emby'
    TelegramId = Column(String(20), ForeignKey('Users.TelegramId'), primary_key=True)
    EmbyId = Column(Text)
    EmbyName = Column(Text)
    LimitDate = Column(DateTime)
    Ban = Column(Boolean, default=False)
    deleteDate = Column(DateTime)
    def __repr__(self):
        return f'<Emby(TelegramId={self.TelegramId}, EmbyId={self.EmbyId}, EmbyName={self.EmbyName}, LimitDate={self.LimitDate}, Ban={self.Ban}, deleteDate={self.deleteDate})>'
    
class Code(Base):
    __tablename__ = 'Codes'
    CodeId = Column(String(255), primary_key=True)
    TimeStamp = Column(Text)
    Tag = Column(Text)
    def __repr__(self):
        return f'<Code(CodeId={self.CodeId}, TimeStamp={self.TimeStamp}), Tag={self.Tag}>'
    
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

async def GetUser(TelegramId):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                user = await session.get(User, TelegramId)
                if user is not None:
                    session.expunge(user)
                    return user
                else:
                    return None
            except Exception as e:
                logging.error(f'Error occurred while getting user {TelegramId}: {e}')
                await session.rollback()
                return None
            
async def CreateUsers(TelegramId):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                if await session.get(User, TelegramId) is None:
                    user = User(TelegramId=TelegramId)
                    session.add(user)
                    await session.commit()
                    return True
                else:
                    return False
            except Exception as e:
                logging.error(f'Error occurred while creating user {TelegramId}: {e}')
                await session.rollback()
                return False

async def DeleteUser(TelegramId):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                user = await session.get(User, TelegramId)
                if user is None:
                    return False
                else:
                    await session.delete(user)
                    await session.commit()
                    return True
            except Exception as e:
                logging.error(f'Error occurred while deleting user {TelegramId}: {e}')
                await session.rollback()
                return False
            
async def ChangeScore(TelegramId, Score):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                user = await session.get(User, TelegramId)
                if user is None:
                    session.add(User(TelegramId=TelegramId, Score=Score))
                else:
                    user.Score += Score
                await session.commit()
                return True
            except Exception as e:
                logging.error(f'Error occurred while changing score of user {TelegramId}: {e}')
                await session.rollback()
                return False

async def ChangeCheckin(TelegramId, Socre=0):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                user = await session.get(User, TelegramId)
                if user is None:
                    session.add(User(TelegramId=TelegramId, Checkin=1, LastCheckin=datetime.now().date(), Score=Socre))
                else:
                    user.Checkin += 1 # type: ignore
                    user.LastCheckin = datetime.now().date() # type: ignore
                    user.Score += Socre # type: ignore
                await session.commit()
                return True
            except Exception as e:
                logging.error(f'Error occurred while changing checkin of user {TelegramId}: {e}')
                await session.rollback()
                return False
            
async def ChangeWarning(TelegramId):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                user = await session.get(User, TelegramId)
                if user is None:
                    session.add(User(TelegramId=TelegramId, Warning=1, Score=-1))
                else:
                    user.Warning += 1 # type: ignore
                    user.Score -= user.Warning # type: ignore
                await session.commit()
                return True
            except Exception as e:
                logging.error(f'Error occurred while changing warning of user {TelegramId}: {e}')
                await session.rollback()
                return False

async def GetEmby(TelegramId):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                emby = await session.get(Emby, TelegramId)
                if emby is not None:
                    session.expunge(emby)
                    return  emby
                else:
                    return None
            except Exception as e:
                logging.error(f'Error occurred while getting emby {TelegramId}: {e}')
                return None
                       
async def CreateEmby(TelegramId, EmbyId, EmbyName):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                if TelegramId in config.other.AdminId:
                    LimitDate = datetime.now() + timedelta(weeks=4752)
                else:
                    LimitDate = datetime.now() + timedelta(days=30)
                if await session.get(Emby, TelegramId) is None:
                    emby = Emby(TelegramId=TelegramId, EmbyId=EmbyId, EmbyName=EmbyName, LimitDate=LimitDate)
                    session.add(emby)
                    await session.commit()
                    return True
                else:
                    return False
            except Exception as e:
                logging.error(f'Error occurred while creating emby {TelegramId}: {e}')
                await session.rollback()
                return False
            
async def DeleteEmby(TelegramId):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                emby = await session.get(Emby, TelegramId)
                if emby is None:
                    return False
                else:
                    await session.delete(emby)
                    await session.commit()
                    return True
            except Exception as e:
                logging.error(f'Error occurred while deleting emby {TelegramId}: {e}')
                await session.rollback()
                return False
            
async def LimitEmbyBan():
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                emby = await session.execute(select(Emby).where(Emby.LimitDate < datetime.now().date(), Emby.Ban == False))
                embyIds = []
                for i in emby.scalars():
                    i.Ban = True
                    i.deleteDate = datetime.now().date() + timedelta(days=7)
                    embyIds.append(i.EmbyId)
                await session.commit()
                return embyIds
            except Exception as e:
                logging.error(f'Error occurred while limiting emby ban: {e}')
                await session.rollback()
                return None
            
async def LimitEmbyDelete():
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                emby = await session.execute(select(Emby).where(Emby.deleteDate < datetime.now().date(), Emby.Ban == True))
                embyIds = []
                for i in emby.scalars():
                    await session.delete(i)
                    embyIds.append(i.EmbyId)
                await session.commit()
                return embyIds
            except Exception as e:
                logging.error(f'Error occurred while limiting emby delete: {e}')
                await session.rollback()
                return None
            
async def UpdateLimitDate(TelegramId, days=30):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                emby = await session.get(Emby, TelegramId)
                if emby is None:
                    return False
                else:
                    if emby.Ban is True:
                        emby.Ban = False
                        emby.LimitDate = datetime.now().date() + timedelta(days=days)
                    else:
                        emby.LimitDate = emby.LimitDate + timedelta(days=days)
                    await session.commit()
                    return True
            except Exception as e:
                logging.error(f'Error occurred while updating limit date of emby {TelegramId}: {e}')
                await session.rollback()
                return False
            
async def CreateCode(CodeId, TimeStamp, Tag):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                session.add(Code(CodeId=CodeId, TimeStamp=TimeStamp, Tag=Tag))
                await session.commit()
                return True
            except Exception as e:
                logging.error(f'Error occurred while creating code {CodeId}: {e}')
                await session.rollback()
                return False
async def GetCode(CodeId):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                code = await session.get(Code, CodeId)
                if code is not None:
                    session.expunge(code)
                    return code
                else:
                    return None
            except Exception as e:
                logging.error(f'Error occurred while getting code {CodeId}: {e}')
                return None
            
async def DeleteCode(CodeId):
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                code = await session.get(Code, CodeId)
                if code is None:
                    return False
                else:
                    await session.delete(code)
                    await session.commit()
                    return True
            except Exception as e:
                logging.error(f'Error occurred while deleting code {CodeId}: {e}')
                await session.rollback()
                return False
            
async def DeleteLimitCode():
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                await session.execute(delete(Code).where(Code.TimeStamp < (datetime.now() - timedelta(days=90)).timestamp()))
                await session.commit()
                return True
            except Exception as e:
                logging.error(f'Error occurred while deleting limit code: {e}')
                await session.rollback()
                return False
            
async def SettleScore(UserRatio, TotalScore):
    renewValue = int(await GetRenewValue())
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                userScore = {}
                for userId, ratio in UserRatio.items():
                    userValue = int(TotalScore * ratio * 0.5)
                    if userValue < 1:
                        userValue = 1
                    user = await session.get(User, userId)
                    if user is None:
                        session.add(User(TelegramId=userId, Score=userValue))
                    else:
                        # n = user.Score // renewValue
                        # result_score = (userValue - n * renewValue) / (n + 1)
                        # sigma_sum = sum(renewValue / i for i in range(1, n + 1))
                        # userValue = result_score + sigma_sum
                        user.Score += userValue
                        
                    userScore[userId] = userValue
                await session.commit()
                return userScore
            except Exception as e:
                logging.error(f'Error occurred while settling score: {e}')
                await session.rollback()
                return None
            
async def GetRenewValue():
    async with AsyncSession(engine) as session:
        async with session.begin():
            try:
                renew = await session.execute(select(func.avg(User.Score)).where(User.Score > 10))
                renew_value = renew.scalar()
                if renew_value is None or renew_value < 100:
                    renew_value = 100
                return renew_value
            except Exception as e:
                logging.error(f'Error occurred while getting renew value: {e}')
                await session.rollback()
                return 100