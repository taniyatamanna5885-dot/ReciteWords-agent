"""词表相关 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import WordList, Word
from services.word_service import get_all_word_lists, get_words_paginated

router = APIRouter(prefix="/api/wordlists", tags=["wordlists"])


@router.get("")
async def list_word_lists(db: AsyncSession = Depends(get_db)):
    """获取所有可用词表"""
    word_lists = await get_all_word_lists(db)
    return [
        {
            "id": wl.id,
            "name": wl.name,
            "display_name": wl.display_name,
            "description": wl.description,
            "word_count": wl.word_count,
            "target": wl.target,
        }
        for wl in word_lists
    ]


@router.get("/{name}/words")
async def get_words(
    name: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """分页获取指定词表的单词"""
    # 查找词表
    result = await db.execute(select(WordList).where(WordList.name == name))
    word_list = result.scalar_one_or_none()
    if not word_list:
        raise HTTPException(status_code=404, detail=f"词表 '{name}' 不存在")

    words, total = await get_words_paginated(db, word_list.id, page, size)
    return {
        "word_list": {
            "id": word_list.id,
            "name": word_list.name,
            "display_name": word_list.display_name,
        },
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
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size,
    }
