import datetime
from sqlalchemy import Date, Column, Integer, ForeignKey, String, Float, DateTime, Text, Boolean, UniqueConstraint, \
    Interval, Table, Enum as SqlEnum, Time
from sqlalchemy.orm import relationship
from database import Base
from enum import Enum as PyEnum, Enum
from domain.group.group_schema import GroupStatus


class FlagStatus(Enum):
    READY = "READY"
    STARTED = "STARTED"
    TERMINATED = "TERMINATED"


class MealTime(Enum):
    BREAKFAST = 1
    BRUNCH = 2  #아점
    LUNCH = 3
    LINNER = 4  #점저
    DINNER = 5
    SNACK = 6  # 간식


Participation = Table(
    'Participation', Base.metadata,
    Column('user_id', Integer, ForeignKey('User.id'), primary_key=True),  ## 그룹가입 user(회원들)
    Column('group_id', Integer, ForeignKey('Group.id'), primary_key=True),  ## 그룹id
    Column('cheating_count', Integer, nullable=True),  ##치팅 횟수
    Column('flag', SqlEnum(FlagStatus, native_enum=False), nullable=False, default=FlagStatus.READY),  # Enum 타입 문자열
    Column('finish_date', Date, nullable=True)  # 실제 종료일 입력
)


class User(Base):  # 회원
    __tablename__ = "User"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String(length=255), nullable=False)  # 회원가입 ID로 쓸 예정 ( 컬럼 이름은 oauth2 form에 맞춰야해서 고정)
    name = Column(String(length=255), nullable=False)  # 실명
    cellphone = Column(String(length=255), unique=True, nullable=False)
    gender = Column(Boolean)  # 1 남자, 0 여자
    birth = Column(DateTime)
    create_date = Column(DateTime, nullable=False)  # 가입일자
    nickname = Column(String(length=255), unique=True, nullable=False)
    rank = Column(String(length=255), nullable=False)
    profile_picture = Column(String(length=255))
    email = Column(String(length=255), unique=True, nullable=False)
    password = Column(String(length=255), nullable=False)
    external_id = Column(String(length=255))  # 연동했을 때 id
    auth_type = Column(String(length=255))  # 연동 방식 ex)kakao
    fcm_token = Column(String(length=255))  # fcm 토큰 -> 앱 실행시(?), 회원가입(?)
    cur_group_id = Column(Integer, ForeignKey("Group.id"))  # 현재 참여중인 그룹 추가
    mentor_id = Column(Integer, ForeignKey("Mentor.id"))
    groups = relationship('Group', secondary=Participation, back_populates='users')


class Mentor(Base):  ## 멘토
    __tablename__ = "Mentor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"), unique=True)
    gym = Column(String(length=255), nullable=True)
    FA = Column(Boolean, nullable=True)
    company_id = Column(Integer, ForeignKey("Company.id"), nullable=True)


class Company(Base):  ## 회사(소속헬스장)
    __tablename__ = "Company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=255), nullable=False)
    owner = Column(String(length=255), nullable=False)
    cellphone = Column(String(length=255), nullable=False)
    certificate = Column(Boolean, nullable=True)


class Suggestion(Base):  ## 개발자에게 의견제출하는 테이블
    __tablename__ = "Suggestion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"))
    title = Column(String(length=255), nullable=False)
    content = Column(Text, nullable=True)
    date = Column(DateTime, nullable=True)


class Track(Base):  # 식단트랙
    __tablename__ = "Track"

    id = Column(Integer, primary_key=True, autoincrement=True)
    icon = Column(String)
    origin_track_id = Column(Integer, ForeignKey("Track.id"))
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    name = Column(String(length=255), default="새로운 식단 트랙")
    water = Column(Float, default=0)
    coffee = Column(Float, default=0)
    alcohol = Column(Float, default=0)
    duration = Column(Integer)  # Interval : 일, 시간, 분, 초 단위로 기간을 표현 가능, 정확한 시간의 간격(기간)
    delete = Column(Boolean, default=False)  # 트랙 생성자가 이를 삭제하면 남들도 이거 사용 못하게 함
    cheating_count = Column(Integer, default=0)
    create_time = Column(DateTime)
    start_date = Column(Date)
    finish_date = Column(Date)
    share_count = Column(Integer, default=0)
    alone = Column(Boolean, default=True)  ## 개인트랙, 공유초대트랙여부
    daily_calorie = Column(Float, default=0)
    routines = relationship("TrackRoutine", back_populates="track")
    # origin_id = Column(Integer, ForeignKey("Track.id"))


class Group(Base):  ## 식단트랙을 사용하고 있는 user 있는지 확인 테이블
    __tablename__ = "Group"

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("Track.id"))
    name = Column(String(length=255))
    creator = Column(Integer, ForeignKey("User.id"), nullable=False)  ## track을 만든 회원의 id
    start_day = Column(Date)
    finish_day = Column(Date)
    status = Column(SqlEnum(GroupStatus), nullable=False)
    users = relationship("User", secondary=Participation, back_populates="groups")


class TrackRoutine(Base):  ## 식단트랙 루틴
    __tablename__ = "TrackRoutine"

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("Track.id"))
    title = Column(String(length=255), nullable=False, default="새로운 루틴")
    calorie = Column(Float, nullable=False, default=0)  # 목표 칼로리
    # week = Column(String(length=255), nullable=True)  ## 요일에 따른 1 2 3 4 5 6 7 == (월 화 수 목 금 토 일)
    # time = Column(String(length=255), nullable=True)  ## 아침, 점심, 저녁 등
    # date = Column(String(length=255), nullable=True)  ## n번째 1,5  9, 14 등
    # repeat = Column(Boolean, nullable=False)  #1은 반복, 0은 단독
    track = relationship("Track", back_populates="routines")
    delete = Column(Boolean, nullable=False, default=False) # 삭제했을 시 true로 변경


#   요일 -> 몇일차인지 확인하는 척도


class TrackRoutineDate(Base):
    __tablename__ = "TrackRoutineDate"
    id = Column(Integer, primary_key=True, autoincrement=True)
    routine_id = Column(Integer, ForeignKey("TrackRoutine.id"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 0 ~ 6
    time = Column(SqlEnum(MealTime), nullable=False, default=MealTime.BREAKFAST)  # MORNING, LUNCH, . . .
    date = Column(Integer, nullable=False)  # 몇일 차 인지
    clock = Column(Time, nullable=False, default=datetime.time(0))


class Invitation(Base):
    __tablename__ = "Invitation"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("Group.id"), nullable=False)
    status = Column(String(length=255), default="pending")


class MealDay(Base):
    __tablename__ = "MealDay"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    water = Column(Float, nullable=True)
    coffee = Column(Float, nullable=True)
    alcohol = Column(Float, nullable=True)
    carb = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    cheating = Column(Integer, nullable=True)
    goalcalorie = Column(Float, nullable=True)  # 목표칼로리
    nowcalorie = Column(Float, nullable=True)  # 현섭취칼로리
    burncalorie = Column(Float, nullable=True)  # 소모칼로리
    gb_carb = Column(String(length=255), nullable=True)  # 탄수화물 구분
    gb_protein = Column(String(length=255), nullable=True)  # 단백질 구분
    gb_fat = Column(String(length=255), nullable=True)  # 지방 구분
    weight = Column(Float, nullable=True)  # 몸무게
    date = Column(Date, nullable=True)  # 등록일자
    routine_success_rate = Column(Float, nullable=True)  # 루틴 지킨 정도
    track_id = Column(Integer, ForeignKey("Track.id"), nullable=True)
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='_user_date_daily_uc'),
    )


class MealHour(Base):  ##식단게시글 (시간대별)
    __tablename__ = "MealHour"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    name = Column(String(length=255), nullable=False)
    picture = Column(String(length=255), nullable=False, index=True)
    text = Column(String(length=255), nullable=True)
    date = Column(DateTime, nullable=False)  ## 등록시점 분단뒤
    heart = Column(Boolean, nullable=True)
    time = Column(SqlEnum(MealTime), nullable=False)  # MORNING, LUNCH, . . .
    carb = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    calorie = Column(Float, nullable=True)  ## 섭취칼로리
    unit = Column(String(length=255), nullable=True)  ##저장단위
    size = Column(Float, nullable=True)  ##사이즈
    track_goal = Column(Boolean, nullable=True)  ##트랙지켯는지 안지켰는지 유무
    label = Column(Integer, nullable=True)
    daymeal_id = Column(Integer, ForeignKey("MealDay.id"), nullable=False)


class Comment(Base):  ##댓글
    __tablename__ = "Comment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meal_id = Column(Integer, ForeignKey("MealHour.id", ondelete="CASCADE"), nullable=False)
    text = Column(String(length=255), nullable=True)
    date = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)  ## 댓글 등록자


class MentorInvite(Base):
    __tablename__ = 'MentorInvite'

    id = Column(Integer, primary_key=True, index=True)
    mentee_id = Column(Integer, ForeignKey('User.id'))
    mentor_id = Column(Integer, ForeignKey('User.id'))
    status = Column(String(length=255), default='pending')  # 'pending', 'accepted', 'rejected'
    mentee = relationship("User", foreign_keys=[mentee_id])
    mentor = relationship("User", foreign_keys=[mentor_id])


class ClearRoutine(Base):
    __tablename__ = 'ClearRoutine'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    mealday_id = Column(Integer, ForeignKey("MealDay.id"))
    group_id = Column(Integer, ForeignKey("Group.id"), nullable=False)
    routine_date_id = Column(Integer, ForeignKey('TrackRoutineDate.id'), nullable=False)
    date = Column(Date, nullable=False) # 루틴 수행할 실제 날짜 -> 2024-09-07
    status = Column(Boolean, default=False)  # 성공 여부
    weekday = Column(Integer, nullable=True)
