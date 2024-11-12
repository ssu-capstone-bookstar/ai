from sqlalchemy import Column, Integer, String, DateTime, Float, Enum, BigInteger, ForeignKey, Boolean
from sqlalchemy.types import LargeBinary
from sqlalchemy.orm import relationship, declarative_base
#from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum
import torch
import torch.nn as nn
from datetime import datetime

Base = declarative_base()

# Enum 정의 (reading_status와 book_category에 대해)
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

# Book 테이블
class Book(Base):
    __tablename__ = 'book'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    book_id = Column(BigInteger, unique=True)
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
    book_category = Column(Enum(BookCategory))

    # Relationship to MemberBook
    member_books = relationship('MemberBook', back_populates='book')
    # Relationship to RecommendingBook
    recommending_books = relationship('RecommendingBook', back_populates='book')

# Member 테이블
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

    # Relationship to MemberBook
    member_books = relationship('MemberBook', back_populates='member')
    # Member와 UserKeyword 관계 설정
    user_keywords = relationship('UserKeyword', back_populates='user')  # 이 유저가 저장한 키워드들

    # Relationship to Recommending (who recommended)
    recommending_books_from = relationship('Recommending', foreign_keys='Recommending.recommender_id', back_populates='recommender')
    # Relationship to Recommending (who was recommended)
    recommended_books = relationship('Recommending', foreign_keys='Recommending.recommended_id', back_populates='recommended')

# MemberBook 테이블 (유저가 읽은 책 정보)
class MemberBook(Base):
    __tablename__ = 'member_book'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    count = Column(Float)
    created_date = Column(DateTime)
    updated_date = Column(DateTime)
    content = Column(String(255))
    read_completion_dates = Column(LargeBinary)
    reading_status = Column(Enum(ReadingStatus))

    # Relationships
    member_id = Column(BigInteger, ForeignKey('member.id'))
    book_id = Column(BigInteger, ForeignKey('book.book_id'))

    member = relationship('Member', back_populates='member_books')
    book = relationship('Book', back_populates='member_books')

# Recommending 테이블 (추천한 유저와 추천받은 유저 간의 관계)
class Recommending(Base):
    __tablename__ = 'recommending'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_date = Column(DateTime)
    updated_date = Column(DateTime)
    recommender_id = Column(BigInteger, ForeignKey('member.id'))  # 추천한 사람
    recommended_id = Column(BigInteger, ForeignKey('member.id'))  # 추천받은 사람
    
    # Relationships
    recommender = relationship('Member', foreign_keys=[recommender_id], back_populates='recommending_books_from')
    recommended = relationship('Member', foreign_keys=[recommended_id], back_populates='recommended_books')
    recommending_books = relationship('RecommendingBook', back_populates='recommending')

# RecommendingBook 테이블 (추천된 책에 대한 정보)
class RecommendingBook(Base):
    __tablename__ = 'recommending_book'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    book_id = Column(BigInteger, ForeignKey('book.book_id'))  # 추천된 책
    recommending_id = Column(BigInteger, ForeignKey('recommending.id'))  # 추천 관계 ID
    created_date = Column(DateTime)
    updated_date = Column(DateTime)
    
    # Relationships
    book = relationship('Book', back_populates='recommending_books')
    recommending = relationship('Recommending', back_populates='recommending_books')


# PyTorch 모델 정의
class RecommenderModel(nn.Module):
    def __init__(self,num_books):
        super(RecommenderModel, self).__init__()
        self.fc1 = nn.Linear(num_books, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, num_books)
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.sigmoid(self.fc3(x))
        return x
    
# UserKeyword 테이블 (유저가 저장한 키워드 정보)
class UserKeyword(Base):
    __tablename__ = 'userkeyword'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)  # 키워드 ID
    user_id = Column(BigInteger, ForeignKey('member.id'), nullable=False)  # 유저 ID (Member 모델과 관계)
    keyword = Column(String(255), nullable=False)  # 키워드
    frequency = Column(Integer, default=1)  # 키워드 빈도수
    created_date = Column(DateTime, default=datetime.utcnow)  # 생성 일자
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 수정 일자

    # Relationships
    user = relationship('Member', back_populates='user_keywords')  # Member 모델과 관계 설정

    def __repr__(self):
        return f"<UserKeyword(user_id={self.user_id}, keyword={self.keyword}, frequency={self.frequency})>"
