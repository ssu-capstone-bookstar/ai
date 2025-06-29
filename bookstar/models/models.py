from enum import Enum as PyEnum
from typing import TYPE_CHECKING

import torch
import torch.nn as nn
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.types import LargeBinary

if TYPE_CHECKING:
    pass

class Base(DeclarativeBase):
    pass

class ReadingStatus(PyEnum):
    READED = "READED"
    READING = "READING"
    WANT_TO_READ = "WANT_TO_READ"

class BookCategory(PyEnum):
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

class Book(Base):
    __tablename__ = 'book'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alading_book_id = Column(BigInteger, unique=True)
    page = Column(Integer)
    published_date = Column(DateTime)
    toc = Column(Integer)
    created_date = Column(DateTime)
    updated_date = Column(DateTime)
    isbn = Column(String(10))
    isbn13 = Column(String(13))
    author = Column(String(255))
    description = Column(String(255))
    publisher = Column(String(255))
    title = Column(String(255))
    book_category: Column[BookCategory] = Column(Enum(BookCategory))
    image_url = Column(String(255))
    
    member_books = relationship('MemberBook', back_populates='book')

class Member(Base):
    __tablename__ = 'member'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    privacy = Column(Boolean)
    created_date = Column(DateTime)
    updated_date = Column(DateTime)
    email = Column(String(50))
    provider_id = Column(String(50))
    nick_name = Column(String(100))
    profile_image = Column(String(255))

    member_books = relationship('MemberBook', back_populates='member')

class MemberBook(Base):
    __tablename__ = 'member_book'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    count = Column(Float)
    created_date = Column(DateTime)
    updated_date = Column(DateTime)
    content = Column(String(255))
    read_completion_dates = Column(LargeBinary)
    reading_status: Column[ReadingStatus] = Column(Enum(ReadingStatus))

    member_id = Column(BigInteger, ForeignKey('member.id'))
    book_id = Column(BigInteger, ForeignKey('book.alading_book_id'))

    member = relationship('Member', back_populates='member_books')
    book = relationship('Book', back_populates='member_books')

# PyTorch 모델
class RecommenderModel(nn.Module):
    def __init__(self, num_books: int) -> None:
        super().__init__()
        self.fc1 = nn.Linear(num_books, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, num_books)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.sigmoid(self.fc3(x))
        return x
