from typing import List

from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Request, Form
from sqlalchemy.sql.functions import current_user
from starlette import status
from datetime import datetime, timedelta
from database import get_db
from domain.user import user_router, user_crud
from domain.user.user_router import get_current_user
from models import Track, User, TrackRoutine
from domain.group import group_crud, group_schema
from domain.track_routine import track_routine_crud, track_routine_schema
from domain.track.track_schema import TrackCreate, TrackResponse, TrackSchema, TrackList
from domain.track import track_crud, track_schema

router = APIRouter(
    prefix="/track",
)


@router.delete("/delete/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_track(track_id: int,
                 db: Session = Depends(get_db),
                 _current_user: User = Depends(get_current_user)):
    track = track_crud.get_track_by_id(db, track_id)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if track.user_id != _current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if track_crud.soft_delete_track(db, track_id) == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="진행중인 트랙 존재")
    return {"status": "ok"}


@router.post("/create", response_model=track_schema.TrackResponse)
def create_track(_current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    """
    트랙 생성,
    기능명세서 p.19 1번 누를때
    """
    track = track_crud.track_create(db, _current_user)
    if track is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="트랙 생성 실패",
        )
    return {"track_id": track.id}


# 트랙 생성 도중에 강제종료 했을 때 예외 처리
@router.patch("/create/next", response_model=track_schema.TrackSchema)
def update_track(_track_id: int,
                 _track: TrackCreate,
                 cheating_cnt: int,
                 _current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    """
    트랙 생성 하기 누를 때 적용 됨, 기능 명세서 p.20
    1. 트랙 내용 채우기
    2. 그룹 생성
    """
    track = track_crud.track_update(db, _track_id, _current_user, _track, cheating_cnt)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    # group = group_crud.create_group(db, track, _current_user.id) 이젠 스타트 할때 생성 할거
    # if group is None:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
    #                         detail="group not found")
    return track


@router.patch("/update/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_track(track_id: int,
                 _track: TrackCreate,
                 cheating_cnt: int,
                 _current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    track = track_crud.get_track_by_id(db, track_id)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if track.delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track state is deleted")

    track_crud.track_update(db, track_id, _current_user, _track, cheating_cnt)


@router.post("/share/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def change_track(track_id: int,
                 _current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    """
    ## 트랙 공유하기
    개인트랙을 하나 복사해서 하나 더 만드는 로직
    """
    track = track_crud.get_track_by_id(db, track_id)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if track.origin_track_id != _current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="트랙 권한이 없음")

    new_track = track_crud.copy_multiple_track(db, track, _current_user.id)
    return new_track


@router.get("/search/{track_name}", response_model=TrackList, status_code=200)
def get_track_by_name(track_name: str, db: Session = Depends(get_db),
                      page: int = 0, size: int = 10):
    """
    # 관련 `키워드` 로 검색
    - 검색 글자 수가 적을 때 사용 하면 좋음.
    ex) `건강` 검색-> `건강한 식단트랙`  (단 두글자 이상 검색해야함)
    """
    track_name.strip()  # 앞뒤 공백 제거
    if len(track_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Track name must be at least 1 character",
        )
    total, tracks = track_crud.get_tracks_by_track_name(db=db, track_name=track_name,
                                                        skip=page * size, limit=size)
    return {
        'total': total,
        'tracks': tracks
    }


# @router.get("/search/{track_name}", response_model=TrackList, status_code=200)
# def get_tracks_by_name_levenshtein(track_name: str, db: Session = Depends(get_db), ):
#     try:
#         track_name.strip()  # 앞뒤 공백 제거
#         track_list = track_crud.search_track_name(db=db, track_name=track_name)
#         return TrackList(
#             total=track_list.count(),
#             tracks=track_list
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#         )


@router.get("/search/lev/{track_name}", response_model=track_schema.TrackSearchResponse, status_code=200)
def get_tracks_by_name_levenshtein(track_name: str, db: Session = Depends(get_db), ):
    """
    ## 검색을 길게 했을 때, 연관 검색어 뜨도록 하는 검색 API
    검색 글자 수가 7글자 이상일 때 사용 하면 좋음.
    """
    if len(track_name) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Track name must be at least 1 character",
        )

    track_name.strip()
    track_list = track_crud.levenshtein_search(track_name, db)
    total = len(track_list)
    return {"total": total, "tracks": track_list}


#@router.get("/get/{track_id}", response_model=TrackSchema, status_code=200)
#def get_track_by_id(track_id: int, db: Session = Depends(get_db)):
#    return track_crud.get_track_by_id(db=db, track_id=track_id)


###################################################

#@router.get("/get/{user_id}", response_model=track_schema.Track_schema)
#def get_Track_id(user_id: int, db: Session = Depends(get_db)):
#    tracks = track_crud.get_Track_byuser_id(db, user_id=user_id)
#    if tracks is None:
#        raise HTTPException(status_code=404, detail="Track not found")
#    return tracks

@router.get("/get/mytracks", response_model=List[track_schema.Track_list_get_schema])
def get_Track_mylist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    보유 트랙 정보 표시 : 19page 2-3번(개인트랙)
     - 입력예시 :
     - 출력 : [Track.id, Track.icon, Track.daily_calorie, Track.name,
               recevied_user_id(트랙공유받은 user_id), recevied_user_name(트랙공유받은 user_name)
             Track.create_time, using:(True,False)]
              ** 공유받은 사람의 id, name이 null이면 개인트랙, 값이 있으면 본인이 공유한트랙
     - 빈출력 = track 없음
     - Track.create_time가 느린순으로 출력
    """
    tracklist = track_crud.get_Track_mine_title_all(db, user_id=current_user.id)
    if tracklist is None:
        raise HTTPException(status_code=404, detail="Track not found")
        return 0
    return tracklist


@router.get("/get/sharetracks", response_model=List[track_schema.Track_list_get_schema])
def get_Track_sharelist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    보유 트랙 정보 표시 : 19page 2-3번(공유한 트랙)
     - 입력예시 :
     - 출력 : [Track.id, Track.icon, Track.daily_calorie, Track.name,
               recevied_user_id(트랙공유받은 user_id), recevied_user_name(트랙공유받은 user_name)
             Track.create_time, using:(True,False)]
              ** 공유받은 사람의 id, name이 null이면 개인트랙, 값이 있으면 본인이 공유한트랙
     - 빈출력 = track 없음
     - Track.create_time가 느린순으로 출력
    """
    tracklist = track_crud.get_Track_share_title_all(db, user_id=current_user.id)
    if tracklist is None:
        raise HTTPException(status_code=404, detail="Track not found")
        return 0
    return tracklist


@router.get("/get/alltracks", response_model=List[track_schema.Track_list_get_schema])
def get_track_all_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    보유 트랙 정보 표시 : 19page 2-3번(초대트랙)(본인트랙 + 공유한 트랙)
     - 입력예시 :
     - 출력 : [Track.id, Track.icon, Track.daily_calorie, Track.name,
               recevied_user_id(트랙공유받은 user_id), recevied_user_name(트랙공유받은 user_name)
             Track.create_time, using:(True,False)]
              ** 공유받은 사람의 id, name이 null이면 개인트랙, 값이 있으면 본인이 공유한트랙
     - 빈출력 = track 없음
     - Track.create_time가 느린순으로 출력
    """
    tracklist = track_crud.get_track_title_all(db, user_id=current_user.id)
    if tracklist is None:
        raise HTTPException(status_code=404, detail="Track not found")
        return 0
    return tracklist


@router.get("/get/{track_id}/Info", response_model=track_schema.Track_get_Info)
def get_Track_Info(track_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    트랙상세보기 : 23page 0번
     - 입력예시 : track_id = 2
     - 출력 : Track.name, User.name, Group.start_date, Group.finish_date, Track.duration, Count(트랙사용중인사람수), [TrackRoutin(반복)],[TrackRoutin(단독)]

     - 홈화면 page1 : 4, 5에도 사용할 수 있을 듯
    """
    ## 루틴반복단독데이터 스키마맞지않음 test필요
    track = track_crud.get_track_by_track_id(db, track_id=track_id)
    if track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    if track.delete:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Track is deleted")

    username = user_crud.get_User_name(db, id=track.user_id)
    today = datetime.utcnow().date() + timedelta(hours=9)

    #트랙을 공유한 횟수
    count = track.share_count

    #그룹 정보여부
    group_one = group_crud.get_group_by_date_track_id_in_part(db, user_id=current_user.id, date=today,
                                                              track_id=track_id)
    if group_one and group_one is not None:
        group, cheating_count, user_id2, flag, finish_date = group_one
        group_startday = group.start_day
        group_finishday = group.finish_day
        real_finishday = finish_date
    else:
        group_startday = None
        group_finishday = None
        real_finishday = None

    # calorie 계산
    calorie = track_routine_crud.get_calorie_average(track_id=track_id, db=db)

    return {
        "track_name": track.name,
        "icon": track.icon,
        "name": username,
        "track_start_day": track.start_date,
        "track_finish_day": track.finish_date,
        "group_start_day": group_startday,
        "group_finish_day": group_finishday,
        "real_finish_day": real_finishday,
        "duration": track.duration,
        "caloire": calorie,
        "count": count,
        "coffee": track.coffee,
        "alcohol": track.alcohol,
        "water": track.water,
        "cheating_count": track.cheating_count,
    }

#@router.post("/post/{user_id})", response_model=track_schema.Track_create_schema)##회원일경우
#def post_Track(user_id: int, track: track_schema.Track_create_schema,db:Session=Depends(get_db)):
#    db_track = Track(
#        user_id=user_id,
#        name=track.name,
#        water=track.water,
#        coffee=track.coffee,
#        alcohol=track.alcohol,
#        duration=track.duration,
#        track_yn=True,
#        cheating_count=track.cheating_count
#    )
#    db.add(db_track)
#    db.commit()
#    db.refresh(db_track)
#
#    for routine in track.routines:
#        db_routine= TrackRoutine(
#            track_id=db_track.id,
#            title=routine.title,
#            food=routine.food,
#            calorie=routine.calorie,
#            week=routine.week,
#            time=routine.time,
#            repeat=routine.repeat
#        )
#        db.add(db_routine)
#
#    db.commit()
#    db.refresh(db_track)


# @router.get("/name/date")
# def get_track_name_date(_date: datetime.date,
#                         current_user: User = Depends(get_current_user),
#                         db:Session = Depends(get_db)):
#     """
#     홈화면 page.3 5번
#     - 트랙 이름, 몇일차이지 가져오기
#     """
#     group = group_crud.get_group_by_id(db, current_user.cur_group_id)
#     if group is None:
#         raise HTTPException(status_code=404, detail="Group not found")
#
#     track = track_crud.get_track_by_id(db, track_id=group.track_id)
#     if track is None:
#         raise HTTPException(status_code=404, detail="Track not found")
#
#     return {"name":track.name, "date":group.start_day - datetime.date().today()}
