from fastapi import FastAPI, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from models import Member, MemberBook, Book
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
        member_books = db.query(MemberBook).filter(MemberBook.member_id == user.user_id).all() or [] 

        read_list = [book.book_id for book in member_books if book.reading_status.value in ["READED", "READING"]]
        want_list = [book.book_id for book in member_books if book.reading_status.value == "WANT_TO_READ"]

        logging.info(f"member_books: {member_books}")
        logging.info(f"read_list: {read_list}")
        logging.info(f"want_list: {want_list}")

        if not read_list and not want_list:
            logging.warning("No books found in MemberBook for the user. Recommending random books.")
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

        recommendation_titles = [book["book_id"] for book in recommendations]
        return {"recommendations": recommendation_titles}

    except Exception as e:
        logging.error(f"Error in get_recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/wordcloud-image")
async def wordcloud_image(user_id: int, image_url: str, db: Session = Depends(get_db)):
    
    keywords = extract_keywords(image_url)
    
    update_user_keywords(user_id, keywords, db)
    
    image_url = create_wordcloud(user_id, db)
    
    return {"wordcloud_url": image_url}