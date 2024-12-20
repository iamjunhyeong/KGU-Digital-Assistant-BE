from http.client import HTTPException
from typing import List

from pygments.lexers import q
from sqlalchemy import desc

from domain.track import track_schema
from models import User, Track, Invitation, MealDay, TrackRoutine, TrackRoutineDate, Group
from sqlalchemy.orm import Session
from domain.track.track_schema import Track_list_get_schema, TrackCreate, TrackSchema
from datetime import datetime, timedelta
from domain.group import group_crud


def track_create(db: Session, user: User):
    db_track = Track(
        user_id=user.id,
        create_time=datetime.now(),
    )
    db.add(db_track)
    db.commit()
    return db_track


# 이름 track 찾기
def track_update(db: Session, _track_id: int, user: User, _track: TrackCreate, cheating_cnt: int):
    track = db.query(Track).filter(Track.id == _track_id).first()
    if (track is None):
        return None
    if (track.user_id != user.id):
        return None

    track.name = _track.name
    track.icon = _track.icon
    track.cheating_count = cheating_cnt
    track.water = _track.water or track.water
    track.coffee = _track.coffee or track.coffee
    track.alcohol = _track.alcohol or track.alcohol
    track.duration = _track.duration
    track.delete = _track.delete
    track.start_date = _track.start_date
    track.end_date = _track.end_date
    track.alone = _track.alone
    track.daily_calorie = _track.calorie
    db.commit()
    db.refresh(track)
    return track


def get_tracks_by_track_name(db: Session, track_name: str, skip: int = 0, limit: int = 10):
    query = db.query(Track).filter(Track.name.contains(track_name)).order_by(desc(Track.name))
    count = query.count()
    tracks = query.offset(skip).limit(limit).all()
    return count, tracks


def get_track_by_id(db: Session, track_id: int):
    return db.query(Track).filter(Track.id == track_id).first()


############################################

def get_Track_byuser_id(db: Session, user_id: int):
    tracks = db.query(Track).filter(
        Track.user_id == user_id
    ).first()
    return tracks


def get_track_by_track_id(db: Session, track_id: int):
    tracks = db.query(Track).filter(
        Track.id == track_id
    ).first()
    return tracks


def get_Track_mine_title_all(db: Session, user_id: int):
    tracks = db.query(Track).filter(Track.user_id == user_id,
                                    Track.delete == False).all()
    tracks = sorted(tracks, key=lambda x: x.create_time, reverse=True)
    return [
        Track_list_get_schema(track_id=track.id, name=track.name, icon=track.icon, daily_calorie=track.daily_calorie,
                              create_time=track.create_time,
                              recevied_user_id=get_user_id_using_track(db, track_id=track.id, user_id=user_id),
                              recevied_user_name=get_user_name_using_track(db, track_id=track.id, user_id=user_id),
                              using=check_today_track_id(db, user_id=user_id, track_id=track.id)) for track in tracks]


def get_Track_share_title_all(db: Session, user_id: int):
    tracks_multi = db.query(Track).filter(Track.user_id == user_id,
                                          Track.delete == False).all()
    tracks = []
    for track_solo in tracks_multi:
        track_share_all = db.query(Track).filter(Track.origin_track_id == track_solo.id).all()
        for track_share_one in track_share_all:
            if track_share_one:
                tracks.append(track_share_one)
    tracks = sorted(tracks, key=lambda x: x.create_time, reverse=True)
    return [
        Track_list_get_schema(track_id=track.id, name=track.name, icon=track.icon, daily_calorie=track.daily_calorie,
                              create_time=track.create_time,
                              recevied_user_id=get_user_id_using_track(db, track_id=track.id, user_id=user_id),
                              recevied_user_name=get_user_name_using_track(db, track_id=track.id, user_id=user_id),
                              using=check_today_track_id(db, user_id=user_id, track_id=track.id)) for track in tracks]


def delete_track(db: Session, track_id: int):
    track = db.query(Track).filter(Track.id == track_id).first()
    db.delete(track)
    db.commit()


def copy_multiple_track(db: Session, track: Track, user_id: int):
    track.share_count += 1
    new_track = Track(
        user_id=user_id,
        origin_track_id=track.id,
        name=track.name,
        water=track.water,
        coffee=track.coffee,
        alcohol=track.alcohol,
        duration=track.duration,
        delete=track.delete,
        start_date=track.start_date,
        finish_date=track.finish_date,
        cheating_count=track.cheating_count,
        alone=False,
        create_time=datetime.now(),
        share_count=track.share_count,
        # origin_id=track.id
    )
    db.add(new_track)
    db.commit()

    routines = db.query(TrackRoutine).filter(TrackRoutine.track_id == track.id).all()
    for routine in routines:
        new_routine = TrackRoutine(
            track_id=new_track.id,
            calorie=routine.calorie,
            repeat=routine.repeat,
            title=routine.title,
            week=routine.week,
            date=routine.date,
        )
        db.add(new_routine)
        db.commit()

    return new_track


def check_today_track_id(db: Session, user_id: int, track_id: int) -> bool:
    date = datetime.utcnow().date() + timedelta(hours=9)
    mealtoday = db.query(MealDay).filter(MealDay.user_id == user_id, MealDay.date == date).first()
    if mealtoday and mealtoday.track_id == track_id:
        return True
    return False


def get_track_title_all(db: Session, user_id: int):
    tracks = []
    #seen_trackid =set() #중복 track_id 확인용
    # 현재 사용자의 track 추가
    trackmine = db.query(Track).filter(Track.user_id == user_id,
                                       Track.delete == False).all()

    # trackmine의 데이터를 tracks에 추가, 중복 제거
    for track in trackmine:
        tracks.append(track)
        #seen_trackid.add(track.id)

    tracks_multi = db.query(Track).filter(Track.user_id == user_id).all()
    for track_solo in tracks_multi:
        track_share_all = db.query(Track).filter(Track.origin_track_id == track_solo.id).all()
        for track_share_one in track_share_all:
            if track_share_one:
                tracks.append(track_share_one)

                #seen_trackid.add(track.id)  # 처리된 track_id 집합

    return [
        Track_list_get_schema(track_id=track.id, name=track.name, icon=track.icon, daily_calorie=track.daily_calorie,
                              create_time=track.create_time,
                              recevied_user_id=get_user_id_using_track(db, track_id=track.id, user_id=user_id),
                              recevied_user_name=get_user_name_using_track(db, track_id=track.id, user_id=user_id),
                              using=check_today_track_id(db, user_id=user_id, track_id=track.id)) for track in tracks]


def get_user_id_using_track(db: Session, track_id: int, user_id: int):
    user_id = db.query(Track.user_id).filter(Track.id == track_id, Track.user_id != user_id).first()
    if user_id is None:
        return None
    return user_id[0]


def get_user_name_using_track(db: Session, track_id: int, user_id: int):
    user_id = get_user_id_using_track(db, track_id=track_id, user_id=user_id)
    if user_id is None:
        return None
    user_name = db.query(User.name).filter(User.id == user_id).first()
    return user_name[0]


def search_track_name(db: Session, track_name: str):
    tracks = db.query(Track).filter(Track.name.like(f"%{track_name}%"),
                                    Track.delete == False).all()
    track_list = []

    for track in tracks:
        track_list.append(track)
    return track_list


def levenshtein_distance(s1: str, s2: str) -> int:
    len_s1, len_s2 = len(s1), len(s2)
    dp = [[0 for _ in range(len_s2 + 1)] for _ in range(len_s1 + 1)]

    for i in range(1, len_s1 + 1):
        dp[i][0] = i
    for j in range(1, len_s2 + 1):
        dp[0][j] = j

    for i in range(1, len_s1 + 1):
        for j in range(1, len_s2 + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1

    return dp[len_s1][len_s2]


def levenshtein_search(_track_name: str, db: Session) -> List[track_schema.TrackSearch]:
    res = []
    tracks = db.query(Track).all()

    for track in tracks:
        dist = levenshtein_distance(str(track.name), _track_name)
        print(dist)
        if dist <= 7:
            res.append(track_schema.TrackSearch(
                id=track.id,
                track_name=track.name,
                score=dist,
            ))

    res.sort(key=lambda x: x.score, reverse=True)

    return res


def soft_delete_track(db:Session, track_id: int):
    db_track = db.query(Track).filter(Track.id == track_id).first()
    groups = db.query(Group).filter(Group.track_id == track_id).all()

    for group in groups:
        if group.start_day <= datetime.utcnow().date() <= group.end_day:
            return 0

    db_track.delete = True

    routines = db.query(TrackRoutine).filter(TrackRoutine.track_id == track_id).all()
    for routine in routines:
        routine.delete = True

    db.commit()
    return 1
