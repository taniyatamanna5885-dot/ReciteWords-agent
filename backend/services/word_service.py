"""单词业务逻辑服务"""
import json
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import DATA_DIR, settings
from models import Word, WordList, WordProgress, StudyRecord


# 已知词表的额外元信息（可选，未列出的词表也能自动加载）
WORDLIST_META = {
    "kaoyan": {"display_name": "考研核心词汇", "description": "考研英语高频核心词汇", "target": "考研"},
    "cet4": {"display_name": "大学英语四级", "description": "CET-4 核心词汇", "target": "四六级"},
    "cet6": {"display_name": "大学英语六级", "description": "CET-6 核心词汇", "target": "四六级"},
    "vocabulary": {"display_name": "自定义词汇", "description": "请自带单词表", "target": ""},
}


def _get_wordlist_meta(name: str) -> dict:
    """获取词表元信息，未配置的词表使用文件名作为显示名"""
    if name in WORDLIST_META:
        return WORDLIST_META[name]
    return {
        "display_name": name.replace("_", " ").replace("-", " ").title(),
        "description": f"自定义词表: {name}",
        "target": "",
    }


async def init_word_lists(db: AsyncSession):
    """初始化词表数据（自动发现 data 目录下所有 JSON 文件，并同步更新）"""
    if not DATA_DIR.exists():
        return

    for json_path in sorted(DATA_DIR.glob("*.json")):
        name = json_path.stem
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                words_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        if not isinstance(words_data, list) or len(words_data) == 0:
            continue

        await _sync_word_list(db, name, words_data)

    await db.commit()


async def _sync_word_list(db: AsyncSession, name: str, words_data: list[dict]):
    """
    同步词表：不存在则创建，存在则增量更新
    - 新增单词 → 插入数据库
    - 已有单词 → 更新释义/音标/例句
    - 更新词表的 word_count
    """
    meta = _get_wordlist_meta(name)

    # 查找或创建词表
    result = await db.execute(select(WordList).where(WordList.name == name))
    word_list = result.scalar_one_or_none()

    if not word_list:
        word_list = WordList(
            name=name,
            display_name=meta["display_name"],
            description=meta["description"],
            word_count=0,
            target=meta["target"],
        )
        db.add(word_list)
        await db.flush()
    else:
        # 同步更新词表元信息
        if word_list.display_name != meta["display_name"]:
            word_list.display_name = meta["display_name"]
        if word_list.description != meta["description"]:
            word_list.description = meta["description"]
        if word_list.target != meta["target"]:
            word_list.target = meta["target"]

    # 获取数据库中已有的单词（按 word 文本去重匹配）
    existing_result = await db.execute(
        select(Word).where(Word.word_list_id == word_list.id)
    )
    existing_words = {w.word.lower(): w for w in existing_result.scalars().all()}

    added = 0
    updated = 0

    for idx, w in enumerate(words_data):
        word_text = w.get("word", "").strip()
        if not word_text:
            continue

        key = word_text.lower()
        if key in existing_words:
            # 已有单词：更新信息（如果变化了）
            ew = existing_words[key]
            changed = False
            if ew.phonetic != w.get("phonetic", ""):
                ew.phonetic = w.get("phonetic", "")
                changed = True
            if ew.meaning != w.get("meaning", ""):
                ew.meaning = w.get("meaning", "")
                changed = True
            if ew.example != w.get("example", ""):
                ew.example = w.get("example", "")
                changed = True
            if ew.order_index != idx:
                ew.order_index = idx
                changed = True
            if changed:
                updated += 1
        else:
            # 新单词：插入
            word = Word(
                word_list_id=word_list.id,
                word=word_text,
                phonetic=w.get("phonetic", ""),
                meaning=w.get("meaning", ""),
                example=w.get("example", ""),
                order_index=idx,
            )
            db.add(word)
            added += 1

    # 更新词表计数
    word_list.word_count = len(words_data)
    await db.flush()

    if added or updated:
        print(f"[词表同步] {name}: +{added} 新增, ~{updated} 更新")


async def import_word_list(db: AsyncSession, name: str, words_data: list[dict],
                           display_name: str = "", description: str = "",
                           target: str = "") -> dict:
    """
    从上传数据导入词表（供 API 调用）
    返回 {"word_list_id": id, "added": n, "updated": n}
    """
    if display_name or description or target:
        # 临时注册元信息
        WORDLIST_META[name] = {
            "display_name": display_name or name,
            "description": description or f"自定义词表: {name}",
            "target": target,
        }

    await _sync_word_list(db, name, words_data)

    # 获取词表 ID
    result = await db.execute(select(WordList).where(WordList.name == name))
    word_list = result.scalar_one()
    await db.commit()

    return {"word_list_id": word_list.id, "word_count": word_list.word_count}


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


async def get_today_study_words(db: AsyncSession, word_list_id: int, count: int | None = None) -> tuple[list[Word], StudyRecord]:
    """
    创建新的学习会话:
    1. 优先返回需要复习的单词
    2. 补充新单词直到达到指定数量
    """
    today = date.today()
    daily_count = count if count and count > 0 else settings.study.daily_word_count

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
