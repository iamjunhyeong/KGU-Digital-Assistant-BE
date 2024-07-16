import datetime


from pydantic import BaseModel

class Comment(BaseModel):
    id: int
    meal_id: int
    text: str
    date: datetime.datetime
    user_id: int

class Comment_id_text(BaseModel):
    user_id: int
    text: str

