#uvicorn main:app --reload
from fastapi import FastAPI
from routers import news, users, favorite, history
from fastapi.middleware.cors import CORSMiddleware
from utils.exception_handlers import register_exception_handlers

app = FastAPI()

#注册异常处理器
register_exception_handlers(app)

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,  #允许的源
    allow_credentials=True,  #运行携带cookie
    allow_methods=["*"],  #允许的请求方法
    allow_headers=["*"],   #允许的请求头
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

#挂载
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)