"""FastAPI 应用入口"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db, async_session
from routers import words, study, generate
from services.word_service import init_word_lists


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期: 启动时初始化数据库和词表"""
    await init_db()
    # 导入词表数据
    async with async_session() as db:
        await init_word_lists(db)
    yield


app = FastAPI(
    title=settings.app_name,
    description="背单词 Agent - AI 生成文章与题目",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置（开发环境允许前端跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(words.router)
app.include_router(study.router)
app.include_router(generate.router)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "app": settings.app_name}
