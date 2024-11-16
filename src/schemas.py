from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


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
    book_id: int
    title: str
    author: str
    book_category: BookCategoryEnum
    description: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[datetime] = None

    class Config:
        from_attributes = True  


class Member(BaseModel):
    id: int
    email: str
    nick_name: Optional[str] = None
    profile_image: Optional[str] = None
    privacy: Optional[bool] = None

    class Config:
        from_attributes = True  


class MemberBook(BaseModel):
    id: int
    count: Optional[float] = None
    content: Optional[str] = None
    reading_status: ReadingStatusEnum
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None

    member_id: int
    book_id: int

    class Config:
        from_attributes = True  


class RecommendationResult(BaseModel):
    book_id: int
    title: str
    author: str
    book_category: BookCategoryEnum
    similarity_score: float 

    class Config:
        from_attributes = True 



class UserRequest(BaseModel):
    user_id: int
    # 추후 read_list 및 recommend_list 필드를 추가해 사용 가능

    class Config:
        from_attributes = True 


class UserKeyword(BaseModel):
    id: int
    user_id: int  # 사용자의 ID
    keyword: str  # 키워드
    frequency: int = 1 # 키워드 빈도수 
    created_date: datetime  # 생성 일자
    updated_date: datetime  # 수정 일자

    class Config:
        from_attributes = True