"""词表相关 API"""
import json
import re

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import DATA_DIR
from database import get_db
from models import WordList, Word
from services.word_service import get_all_word_lists, get_words_paginated, import_word_list

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


@router.post("/upload")
async def upload_word_list(
    file: UploadFile,
    name: str = Query("", description="指定词表名称，为空则使用文件名"),
    db: AsyncSession = Depends(get_db),
):
    """上传自定义词表 JSON 文件"""
    # 检查文件类型
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="请上传 .json 文件")

    # 读取并解析
    try:
        content = await file.read()
        words_data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="JSON 格式不正确")

    if not isinstance(words_data, list) or len(words_data) == 0:
        raise HTTPException(status_code=400, detail="JSON 应为单词数组且不为空")

    # 验证数据格式
    for i, w in enumerate(words_data):
        if not isinstance(w, dict) or "word" not in w or "meaning" not in w:
            raise HTTPException(
                status_code=400,
                detail=f"第 {i+1} 条数据缺少必要字段(word/meaning)"
            )

    # 使用指定名称或从文件名生成
    if not name:
        name = re.sub(r'[^\w\-]', '_', file.filename.replace('.json', ''))

    # 保存文件到 data 目录
    save_path = DATA_DIR / f"{name}.json"
    DATA_DIR.mkdir(exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(words_data, f, ensure_ascii=False, indent=2)

    # 导入数据库
    result = await import_word_list(db, name, words_data)

    return {
        "success": True,
        "name": name,
        "word_list_id": result["word_list_id"],
        "word_count": result["word_count"],
    }


@router.delete("/{name}")
async def delete_word_list(
    name: str,
    db: AsyncSession = Depends(get_db),
):
    """删除词表（同时删除数据库记录和 JSON 文件）"""
    result = await db.execute(select(WordList).where(WordList.name == name))
    word_list = result.scalar_one_or_none()
    if not word_list:
        raise HTTPException(status_code=404, detail="词表不存在")

    # 删除数据库中的单词
    words_result = await db.execute(select(Word).where(Word.word_list_id == word_list.id))
    for w in words_result.scalars().all():
        await db.delete(w)

    # 删除词表
    await db.delete(word_list)

    # 删除 JSON 文件
    json_path = DATA_DIR / f"{name}.json"
    if json_path.exists():
        json_path.unlink()

    await db.commit()
    return {"success": True}
