# test main.py
from fastapi import FastAPI

app = FastAPI()


@app.get("/hello")
def hello():
    return {"message": "안녕하세요 파이보"}