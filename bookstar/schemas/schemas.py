from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ReadingStatusEnum(str, Enum):
    READED = "READED"
    READING = "READING"
    WANT_TO_READ = "WANT_TO_READ"


class BookCategoryEnum(str, Enum):
    ART = "ART"
    CHILDREN = "CHILDREN"
    COMICS = "COMICS"
    COOKING = "COOKING"
    ECONOMICS = "ECONOMICS"
    EDUCATION = "EDUCATION"
    ESSAY = "ESSAY"
    HEALTH = "HEALTH"
    HISTORY = "HISTORY"
    LITERATURE = "LITERATURE"
    MUSIC = "MUSIC"
    NOVEL = "NOVEL"
    OTHER = "OTHER"
    PHILOSOPHY = "PHILOSOPHY"
    POETRY = "POETRY"
    POLITICS = "POLITICS"
    RELIGION = "RELIGION"
    SCIENCE = "SCIENCE"
    SELF_HELP = "SELF_HELP"
    TECHNOLOGY = "TECHNOLOGY"
    TRAVEL = "TRAVEL"


class Book(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    alading_book_id: int
    title: str
    author: str
    book_category: BookCategoryEnum
    description: str | None = None
    publisher: str | None = None
    published_date: datetime | None = None
    image_url: str | None = None


class Member(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    nick_name: str | None = None
    profile_image: str | None = None
    privacy: bool | None = None


class MemberBook(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    count: float | None = None
    content: str | None = None
    reading_status: ReadingStatusEnum
    created_date: datetime | None = None
    updated_date: datetime | None = None

    member_id: int
    book_id: int


class RecommendationResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    book_id: int
    title: str
    author: str
    book_category: BookCategoryEnum
    similarity_score: float


class UserRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    # 추후 read_list 및 recommend_list 필드를 추가해 사용 가능


class UserKeyword(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int  # 사용자의 ID
    keyword: str  # 키워드
    frequency: int = 1  # 키워드 빈도수
    created_date: datetime  # 생성 일자
    updated_date: datetime  # 수정 일자