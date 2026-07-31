"""学习进度相关 API"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import WordList, Word, StudyRecord
from services.word_service import (
    get_today_study_words,
    mark_word_progress,
    complete_study_record,
)

router = APIRouter(prefix="/api/study", tags=["study"])


class MarkRequest(BaseModel):
    """标记单词请求"""
    word_id: int
    word_list_id: int
    known: bool  # True=认识, False=不认识


class CompleteRequest(BaseModel):
    """完成学习请求"""
    record_id: int


@router.get("/today")
async def get_today_words(
    word_list_id: int,
    count: int = Query(0, ge=0, le=200, description="学习数量，0表示仅查询不创建记录"),
    db: AsyncSession = Depends(get_db),
):
    """获取今日学习单词"""
    # 验证词表存在
    result = await db.execute(select(WordList).where(WordList.id == word_list_id))
    word_list = result.scalar_one_or_none()
    if not word_list:
        raise HTTPException(status_code=404, detail="词表不存在")

    word_list_info = {
        "id": word_list.id,
        "name": word_list.name,
        "display_name": word_list.display_name,
        "target": word_list.target,
    }

    # count=0: 仅返回词表信息，不创建记录也不查历史
    if count == 0:
        return {
            "record_id": None,
            "study_date": str(date.today()),
            "status": "not_started",
            "word_list": word_list_info,
            "words": [],
            "total": 0,
            "total_available": word_list.word_count,
        }

    # count>0: 创建或获取学习记录
    words, record = await get_today_study_words(db, word_list_id, count=count)

    return {
        "record_id": record.id,
        "study_date": str(record.study_date),
        "status": record.status,
        "word_list": word_list_info,
        "words": [
            {
                "id": w.id,
                "word": w.word,
                "phonetic": w.phonetic,
                "meaning": w.meaning,
                "example": w.example,
            }
            for w in words
        ],
        "total": len(words),
        "total_available": word_list.word_count,
    }


@router.post("/mark")
async def mark_word(req: MarkRequest, db: AsyncSession = Depends(get_db)):
    """标记单词掌握状态"""
    await mark_word_progress(db, req.word_id, req.word_list_id, req.known)
    return {"success": True, "word_id": req.word_id, "known": req.known}


@router.post("/complete")
async def complete_study(req: CompleteRequest, db: AsyncSession = Depends(get_db)):
    """完成今日学习"""
    await complete_study_record(db, req.record_id)
    return {"success": True, "record_id": req.record_id}


@router.get("/history")
async def get_history(
    word_list_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取学习历史"""
    result = await db.execute(
        select(StudyRecord)
        .where(StudyRecord.word_list_id == word_list_id)
        .order_by(StudyRecord.study_date.desc())
        .limit(30)
    )
    records = list(result.scalars().all())
    return [
        {
            "id": r.id,
            "study_date": str(r.study_date),
            "status": r.status,
            "word_count": len(r.word_id_list),
        }
        for r in records
    ]
