from fastapi import FastAPI, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from models import Member, MemberBook, Book, Recommending, RecommendingBook
from wordcloud_utils import extract_keywords, update_user_keywords, create_wordcloud
from schemas import UserRequest
from db_connection import get_db
from recommendation import recommend_books  
import logging
from fastapi.responses import JSONResponse
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


@app.post("/wordcloud-image")
async def wordcloud_image(user_id: int, image_url: str, db: Session = Depends(get_db)):
    
    # 1. 이미지를 통해 키워드 추출
    keywords = extract_keywords(image_url)
    
    # 2. 추출된 키워드 데이터베이스에 저장
    update_user_keywords(user_id, keywords, db)
    
    # 3. 새로운 키워드를 바탕으로 워드 클라우드 생성
    image_url = create_wordcloud(user_id, db)
    
    # 4. 워드 클라우드 이미지 URL 반환
    return {"wordcloud_url": image_url}