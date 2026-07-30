"""单词业务逻辑服务"""
import json
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import DATA_DIR, settings
from models import Word, WordList, WordProgress, StudyRecord


# 词表元信息
WORDLIST_META = {
    "kaoyan": {"display_name": "考研核心词汇", "description": "考研英语高频核心词汇", "target": "考研"},
    "cet4": {"display_name": "大学英语四级", "description": "CET-4 核心词汇", "target": "四六级"},
    "cet6": {"display_name": "大学英语六级", "description": "CET-6 核心词汇", "target": "四六级"},
}


async def init_word_lists(db: AsyncSession):
    """初始化词表数据（从 JSON 文件导入）"""
    for name, meta in WORDLIST_META.items():
        # 检查是否已存在
        result = await db.execute(select(WordList).where(WordList.name == name))
        if result.scalar_one_or_none():
            continue

        json_path = DATA_DIR / f"{name}.json"
        if not json_path.exists():
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            words_data = json.load(f)

        # 创建词表
        word_list = WordList(
            name=name,
            display_name=meta["display_name"],
            description=meta["description"],
            word_count=len(words_data),
            target=meta["target"],
        )
        db.add(word_list)
        await db.flush()

        # 导入单词
        for idx, w in enumerate(words_data):
            word = Word(
                word_list_id=word_list.id,
                word=w["word"],
                phonetic=w.get("phonetic", ""),
                meaning=w["meaning"],
                example=w.get("example", ""),
                order_index=idx,
            )
            db.add(word)

    await db.commit()


async def get_all_word_lists(db: AsyncSession) -> list[WordList]:
    """获取所有词表"""
    result = await db.execute(select(WordList).order_by(WordList.id))
    return list(result.scalars().all())


async def get_words_paginated(
    db: AsyncSession, word_list_id: int, page: int = 1, size: int = 20
) -> tuple[list[Word], int]:
    """分页获取词表中的单词"""
    # 总数
    count_result = await db.execute(
        select(Word).where(Word.word_list_id == word_list_id)
    )
    total = len(count_result.all())

    # 分页
    offset = (page - 1) * size
    result = await db.execute(
        select(Word)
        .where(Word.word_list_id == word_list_id)
        .order_by(Word.order_index)
        .offset(offset)
        .limit(size)
    )
    words = list(result.scalars().all())
    return words, total


async def get_today_study_words(db: AsyncSession, word_list_id: int) -> tuple[list[Word], StudyRecord]:
    """
    获取今日学习单词:
    1. 优先返回需要复习的单词
    2. 补充新单词直到达到每日数量
    """
    today = date.today()
    daily_count = settings.study.daily_word_count

    # 检查今天是否已有学习记录
    result = await db.execute(
        select(StudyRecord).where(
            and_(
                StudyRecord.study_date == today,
                StudyRecord.word_list_id == word_list_id,
            )
        )
    )
    record = result.scalar_one_or_none()

    if record and record.status == "completed":
        # 今天已完成，返回已学单词
        word_ids = record.word_id_list
        words_result = await db.execute(
            select(Word).where(Word.id.in_(word_ids))
        )
        return list(words_result.scalars().all()), record

    if record:
        # 今天有未完成的记录，继续
        word_ids = record.word_id_list
        words_result = await db.execute(
            select(Word).where(Word.id.in_(word_ids))
        )
        return list(words_result.scalars().all()), record

    # 创建新的学习记录
    # 1. 获取需要复习的单词
    review_result = await db.execute(
        select(WordProgress).where(
            and_(
                WordProgress.word_list_id == word_list_id,
                WordProgress.next_review_date <= today,
                WordProgress.familiarity < 5,
            )
        ).limit(daily_count // 2)
    )
    review_progress = list(review_result.scalars().all())
    review_word_ids = [p.word_id for p in review_progress]

    # 2. 获取新单词（未学过的）
    new_count = daily_count - len(review_word_ids)
    learned_result = await db.execute(
        select(WordProgress.word_id).where(
            WordProgress.word_list_id == word_list_id
        )
    )
    learned_ids = [row[0] for row in learned_result.all()]

    new_query = select(Word).where(
        and_(
            Word.word_list_id == word_list_id,
        )
    )
    if learned_ids:
        new_query = new_query.where(Word.id.notin_(learned_ids))
    new_query = new_query.order_by(Word.order_index).limit(new_count)

    new_result = await db.execute(new_query)
    new_words = list(new_result.scalars().all())

    # 合并
    all_word_ids = review_word_ids + [w.id for w in new_words]

    # 获取完整单词对象
    if review_word_ids:
        review_words_result = await db.execute(
            select(Word).where(Word.id.in_(review_word_ids))
        )
        review_words = list(review_words_result.scalars().all())
    else:
        review_words = []

    all_words = review_words + new_words

    # 创建学习记录
    record = StudyRecord(
        study_date=today,
        word_list_id=word_list_id,
        status="in_progress",
    )
    record.word_id_list = all_word_ids
    db.add(record)
    await db.flush()

    return all_words, record


async def mark_word_progress(
    db: AsyncSession,
    word_id: int,
    word_list_id: int,
    known: bool,
):
    """标记单词掌握状态"""
    today = date.today()

    # 查找或创建进度记录
    result = await db.execute(
        select(WordProgress).where(
            and_(
                WordProgress.word_id == word_id,
                WordProgress.word_list_id == word_list_id,
            )
        )
    )
    progress = result.scalar_one_or_none()

    if not progress:
        progress = WordProgress(
            word_id=word_id,
            word_list_id=word_list_id,
            familiarity=0,
            review_count=0,
        )
        db.add(progress)

    progress.last_study_date = today
    progress.review_count += 1

    if known:
        progress.familiarity = min(5, progress.familiarity + 1)
    else:
        progress.familiarity = max(0, progress.familiarity - 1)

    # 计算下次复习时间
    intervals = settings.study.review_interval_days
    idx = min(progress.familiarity, len(intervals) - 1)
    progress.next_review_date = today + timedelta(days=intervals[idx])

    await db.flush()


async def complete_study_record(db: AsyncSession, record_id: int):
    """完成学习记录"""
    result = await db.execute(
        select(StudyRecord).where(StudyRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if record:
        record.status = "completed"
        await db.flush()
