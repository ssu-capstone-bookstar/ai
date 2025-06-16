import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from bookstar.config import settings
from bookstar.database.connection import get_db
from bookstar.models.models import MemberBook
from bookstar.schemas.schemas import UserRequest
from bookstar.services.recommendation import recommend_books

logging.basicConfig(level=getattr(logging, settings.app['log_level']))
app = FastAPI(title="BookStar AI", description="AI 기반 도서 추천 시스템")

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app['cors_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/recommend_books")
async def get_recommendations(user: UserRequest, db: Session = Depends(get_db)):
    try:
        member_books = (
            db.query(MemberBook)
            .filter(MemberBook.member_id == user.user_id)
            .all() or []
        )

        read_list = [
            str(book.book_id) 
            for book in member_books 
            if book.reading_status.value in ["READED", "READING"]
        ]
        want_list = [
            str(book.book_id) 
            for book in member_books 
            if book.reading_status.value == "WANT_TO_READ"
        ]

        logging.info(f"member_books: {member_books}")
        logging.info(f"read_list: {read_list}")
        logging.info(f"want_list: {want_list}")

        if not read_list and not want_list:
            logging.warning(
                "No books found in MemberBook for the user. "
                "Recommending random books."
            )
            recommendations = recommend_books(
                db=db,
                user_id=user.user_id,
                read_list=[],
                want_list=[],
                num_recommendations=10 
            )
        else:
            recommendations = recommend_books(
                db=db,
                user_id=user.user_id,
                read_list=read_list,
                want_list=want_list,
                num_recommendations=10
            )

        return {"recommendations": recommendations}

    except Exception as e:
        logging.error(f"Error in get_recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e