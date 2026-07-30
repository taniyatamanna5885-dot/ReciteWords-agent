"""SQLAlchemy 数据模型"""
import json
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class WordList(Base):
    """词表"""
    __tablename__ = "word_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    target: Mapped[str] = mapped_column(String(50), default="")  # 目标考试: kaoyan/cet4/cet6


class Word(Base):
    """单词"""
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_list_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    word: Mapped[str] = mapped_column(String(100), nullable=False)
    phonetic: Mapped[str] = mapped_column(String(100), default="")
    meaning: Mapped[str] = mapped_column(String(500), nullable=False)
    example: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)  # 在词表中的顺序


class StudyRecord(Base):
    """每日学习记录"""
    __tablename__ = "study_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    word_list_id: Mapped[int] = mapped_column(Integer, nullable=False)
    word_ids: Mapped[str] = mapped_column(Text, default="[]")  # JSON array of word ids
    status: Mapped[str] = mapped_column(String(20), default="in_progress")  # in_progress / completed
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @property
    def word_id_list(self) -> list[int]:
        return json.loads(self.word_ids)

    @word_id_list.setter
    def word_id_list(self, ids: list[int]):
        self.word_ids = json.dumps(ids)


class WordProgress(Base):
    """单词学习进度"""
    __tablename__ = "word_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    word_list_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    familiarity: Mapped[int] = mapped_column(Integer, default=0)  # 0-5 熟悉程度
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_study_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class GeneratedContent(Base):
    """AI 生成的文章和题目"""
    __tablename__ = "generated_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    study_record_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    article: Mapped[str] = mapped_column(Text, default="")
    questions: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @property
    def questions_list(self) -> list:
        return json.loads(self.questions)

    @questions_list.setter
    def questions_list(self, data: list):
        self.questions = json.dumps(data, ensure_ascii=False)
