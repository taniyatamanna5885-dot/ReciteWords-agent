"""AI 生成文章/题目 API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Word, WordList, StudyRecord, GeneratedContent
from services.generate_service import generate_article, generate_questions

router = APIRouter(prefix="/api/generate", tags=["generate"])


class GenerateArticleRequest(BaseModel):
    """生成文章请求"""
    study_record_id: int


class GenerateQuestionsRequest(BaseModel):
    """生成题目请求"""
    study_record_id: int


@router.post("/article")
async def api_generate_article(
    req: GenerateArticleRequest,
    db: AsyncSession = Depends(get_db),
):
    """基于今日单词生成文章"""
    # 获取学习记录
    result = await db.execute(
        select(StudyRecord).where(StudyRecord.id == req.study_record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="学习记录不存在")

    # 获取词表信息（目标考试）
    wl_result = await db.execute(
        select(WordList).where(WordList.id == record.word_list_id)
    )
    word_list = wl_result.scalar_one_or_none()
    target = word_list.target if word_list else "考研"

    # 获取单词详情
    word_ids = record.word_id_list
    words_result = await db.execute(select(Word).where(Word.id.in_(word_ids)))
    words = list(words_result.scalars().all())

    if not words:
        raise HTTPException(status_code=400, detail="没有可生成文章的单词")

    # 调用 LLM 生成文章
    words_data = [{"word": w.word, "meaning": w.meaning} for w in words]
    try:
        article = await generate_article(words_data, target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文章生成失败: {str(e)}")

    # 保存生成内容
    # 检查是否已有记录
    existing = await db.execute(
        select(GeneratedContent).where(
            GeneratedContent.study_record_id == req.study_record_id
        )
    )
    content = existing.scalar_one_or_none()
    if content:
        content.article = article
    else:
        content = GeneratedContent(
            study_record_id=req.study_record_id,
            article=article,
        )
        db.add(content)
    await db.flush()

    return {
        "id": content.id,
        "study_record_id": req.study_record_id,
        "article": article,
        "word_count": len(words),
    }


@router.post("/questions")
async def api_generate_questions(
    req: GenerateQuestionsRequest,
    db: AsyncSession = Depends(get_db),
):
    """基于已生成文章生成题目"""
    # 获取学习记录
    result = await db.execute(
        select(StudyRecord).where(StudyRecord.id == req.study_record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="学习记录不存在")

    # 获取已生成的文章
    content_result = await db.execute(
        select(GeneratedContent).where(
            GeneratedContent.study_record_id == req.study_record_id
        )
    )
    content = content_result.scalar_one_or_none()
    if not content or not content.article:
        raise HTTPException(status_code=400, detail="请先生成文章")

    # 获取目标考试
    wl_result = await db.execute(
        select(WordList).where(WordList.id == record.word_list_id)
    )
    word_list = wl_result.scalar_one_or_none()
    target = word_list.target if word_list else "考研"

    # 调用 LLM 生成题目
    try:
        questions = await generate_questions(content.article, target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"题目生成失败: {str(e)}")

    # 保存题目
    content.questions_list = questions
    await db.flush()

    return {
        "id": content.id,
        "study_record_id": req.study_record_id,
        "questions": questions,
    }


@router.get("/content/{study_record_id}")
async def get_generated_content(
    study_record_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取已生成的内容"""
    result = await db.execute(
        select(GeneratedContent).where(
            GeneratedContent.study_record_id == study_record_id
        )
    )
    content = result.scalar_one_or_none()
    if not content:
        return {"article": None, "questions": []}

    return {
        "id": content.id,
        "article": content.article,
        "questions": content.questions_list,
        "created_at": str(content.created_at) if content.created_at else None,
    }
