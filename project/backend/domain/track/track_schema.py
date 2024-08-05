from typing import List, Optional
from datetime import date,datetime
from fastapi.openapi.models import Schema
from pydantic import BaseModel
from sqlalchemy import Interval
from domain.track_routine.track_routine_schema import  TrackRoutineCreateSchema, TrackRoutin_id_title


class TrackCreate(BaseModel):
    name: str
    water: float
    coffee: float
    alcohol: float
    duration: int
    track_yn: bool
    alone: bool
    start_date: date
    end_date: date

    class Config:
        orm_mode = True

    # user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    # name = Column(String, nullable=False)
    # water = Column(Float)
    # coffee = Column(Float)
    # alcohol = Column(Float)
    # duration = Column(Interval)  # Interval : 일, 시간, 분, 초 단위로 기간을 표현 가능, 정확한 시간의 간격(기간)
    # track_yn = Column(Boolean,

class TrackResponse(BaseModel):
    track_id: int


# 이거 원본이랑 column 이름까지 같아야함
class TrackSchema(BaseModel):
    id: int
    user_id: int
    name: str
    water: float
    coffee: float
    alcohol: float
    duration: int
    track_yn: bool

    class Config:
        orm_mode = True


class TrackList(BaseModel):
    total: int = 0
    tracks: list[TrackSchema] = []


######################################
class Track_schema(BaseModel):
    id: int
    user_id: int
    name: str
    water: Optional[float] = None
    coffee: Optional[float] = None
    alcohol: Optional[float] = None
    duration: Optional[int] = None
    track_yn: bool
    cheating_count: Optional[int] = None

class Track_list_get_schema(BaseModel):
    track_id: int
    name: str
    create_time: datetime
    using: Optional[bool] = None

class Track_create_schema(BaseModel):
    name: str
    water: float
    coffee: float
    alcohol: float
    start_date: date
    finish_date: date
    routines: List[TrackRoutineCreateSchema] = []

class Track_get_Info(BaseModel):
    track_name: str
    name: str
    track_start_day: Optional[date]=None
    track_finish_day: Optional[date]= None
    group_start_day: Optional[date]=None
    group_finish_day: Optional[date]= None
    real_finish_day: Optional[date]=None
    duration: Optional[int]= None
    calorie: Optional[float] = None
    count: Optional[int]=None
    coffee: Optional[float] = None
    alcohol: Optional[float] = None
    water: Optional[float] = None
    repeatroutin: Optional[List[TrackRoutin_id_title]] = []
    soloroutin: Optional[List[TrackRoutin_id_title]] = []

