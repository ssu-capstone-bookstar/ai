from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Member, MemberBook, Book, Recommending, RecommendingBook
from schemas import UserRequest
from db_connection import get_db
from recommendation import recommend_books  
import logging

logging.basicConfig(level=logging.INFO)
app = FastAPI()

@app.post("/recommend_books")
async def get_recommendations(user: UserRequest, db: Session = Depends(get_db)):
    try:
        # user_id에 해당하는 MemberBook 레코드 가져오기
        member_books = db.query(MemberBook).filter(MemberBook.member_id == user.user_id).all() or [] 

        if not member_books:
            raise HTTPException(status_code=404, detail="No books found for the user")

        # 각각의 리스트 생성
        read_list = [book.book_id for book in member_books if book.reading_status.value in ["READED", "READING"]]
        want_list = [book.book_id for book in member_books if book.reading_status.value == "WANT_TO_READ"]

        # 로그 출력
        logging.info(f"member_books: {member_books}")
        logging.info(f"read_list: {read_list}")
        logging.info(f"want_list: {want_list}")

        # 추천 시스템 호출
        recommendations = recommend_books(
            db=db,
            user_id=user.user_id,
            read_list=read_list,
            want_list=want_list,
            num_recommendations=10
        )

        # 추천 결과에서 title만 추출하여 반환
        recommendation_titles = [book["title"] for book in recommendations]
        return {"recommendations": recommendation_titles}

    except Exception as e:
        logging.error(f"Error in get_recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
