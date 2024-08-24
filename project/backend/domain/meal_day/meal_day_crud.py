from datetime import datetime, date

from domain.meal_day.meal_day_schema import Mealday_wca_update_schema
from models import MealDay

from sqlalchemy.orm import Session
from fastapi import HTTPException

def get_MealDay_bydate(db: Session, user_id: int, date: date):
    mealDaily = db.query(MealDay).filter(
        MealDay.user_id == user_id,
        MealDay.date == date).first()
    if mealDaily is None:
        return None
    return mealDaily

def get_MealDay_bydate_cheating(db: Session, user_id: int, date: datetime):
    mealDaily = db.query(MealDay.cheating).filter(
        MealDay.user_id == user_id,
        MealDay.date == date).first()
    if mealDaily:
        return mealDaily

def get_MealDay_bydate_wca(db: Session, user_id: int, date: date):
    mealDaily = db.query(
        MealDay.water,
        MealDay.coffee,
        MealDay.alcohol
    ).filter(
        MealDay.user_id == user_id,
        MealDay.date == date
    ).first()
    if mealDaily:
        return mealDaily
    return None

def update_wca(db: Session, db_MealPosting_Daily: MealDay,
                       wca_update: Mealday_wca_update_schema):
    db_MealPosting_Daily.water =wca_update.water
    db_MealPosting_Daily.coffee=wca_update.coffee
    db_MealPosting_Daily.alcohol=wca_update.alcohol
    db.add(db_MealPosting_Daily)
    db.commit()

def get_MealDay_bydate_calorie(db: Session, user_id: int, date: date):
    mealDaily = db.query(
        MealDay.goalcalorie,
        MealDay.nowcalorie
    ).filter(
        MealDay.user_id == user_id,
        MealDay.date == date
    ).first()
    if mealDaily:
        return mealDaily
    return None