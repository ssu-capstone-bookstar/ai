from fastapi import FastAPI, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from models import Member, MemberBook, Book
from wordcloud_utils import extract_keywords, update_user_keywords, create_wordcloud, generate_presigned_url, BUCKET_NAME, object_exists
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

        recommendation_data = [{"book_id":book["book_id"],"title":book["title"]} for book in recommendations]
        return {"recommendations": recommendation_data}

    except Exception as e:
        logging.error(f"Error in get_recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

#wordcloud 새로 업데이트 할 경우 == 스크랩했을 경우
@app.post("/wordcloud-image")
async def wordcloud_image(user_id: int, image_url: str, db: Session = Depends(get_db)):
    
    keywords = extract_keywords(image_url)
    
    update_user_keywords(user_id, keywords, db)
    
    image_url = create_wordcloud(user_id, db) 
    
    return {"wordcloud_url": image_url}  
    #return {"keyword":keywords} // 텍스트 확인용 

#wordcloud 이미지 불러올 경우 
@app.get('/generate-presigned-url') #프론트에서 이미지 url 필요할때 
def get_presigned_url(user_id:int):
    file_name = f"wordclouds/{user_id}/wordcloud_{user_id}.png"
    # S3에 해당 객체가 존재하는지 확인
    if not object_exists(BUCKET_NAME, file_name):
        return JSONResponse({'url': None})
    
    presigned_url = generate_presigned_url(BUCKET_NAME, file_name)

    if presigned_url:
        return JSONResponse({'url': presigned_url})
    else:
        return JSONResponse({'error': 'Failed to generate presigned URL'}), 500