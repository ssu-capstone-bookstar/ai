import boto3
import os
import re
from collections import Counter
from wordcloud import WordCloud
from tempfile import NamedTemporaryFile
from sqlalchemy.orm import Session
import easyocr
from models import UserKeyword
from datetime import datetime
from io import BytesIO
import requests
import numpy as np
import cv2
from easyocr import Reader

# AWS S3 환경 설정
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
BUCKET_NAME = os.getenv("BUCKET_NAME", "database1")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

ocr = easyocr.Reader(['ko', 'en'])
font_path = "C:\\Users\\kelly\\Documents\\AI\\nanum-all\\NanumGothic.ttf"

# 텍스트 전처리
def preprocess_text(text):
    text = re.sub(r'[^\w\s]', '', text)  # 특수문자 제거
    tokens = text.lower().split()  # 소문자화 및 단어 분리
    stopwords = {"은", "는", "이", "가", "의", "에"}  # 불용어
    return [word for word in tokens if word not in stopwords]

# OCR을 통해 텍스트 추출
def extract_keywords(image_url: str):
    # 이미지 다운로드
    response = requests.get(image_url)
    image_bytes = BytesIO(response.content)
    
    # 이미지를 OpenCV 형식으로 변환 (easyocr는 numpy array를 받음)
    image_np = np.array(bytearray(image_bytes.read()), dtype=np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    
    # EasyOCR 리더 초기화
    ocr = Reader(['en'])  # 영어 OCR 리더 초기화
    
    # OCR로 텍스트 추출
    extracted_text = ocr.readtext(image, detail=0)
    
    # 텍스트 전처리
    return preprocess_text(" ".join(extracted_text))
# 키워드 업데이트 (테이블에 키워드 저장 및 빈도수 증가)
def update_user_keywords(user_id: int, keywords: list, db: Session):
    keyword_counts = Counter(keywords)
    for keyword, count in keyword_counts.items():
        db_keyword = db.query(UserKeyword).filter_by(user_id=user_id, keyword=keyword).first()
        if db_keyword:
            db_keyword.frequency += count  # 이미 키워드가 있으면 빈도수만 증가
        else:
            # 새로운 키워드인 경우 삽입
            db.add(UserKeyword(user_id=user_id, keyword=keyword, frequency=count))
    db.commit()

# 워드 클라우드 생성 및 S3에 업로드
def create_wordcloud(user_id: int, db: Session):
    # 사용자 키워드 가져오기
    keyword_data = db.query(UserKeyword).filter_by(user_id=user_id).all()
    keyword_counter = Counter({kw.keyword: kw.frequency for kw in keyword_data})
    
    # 워드 클라우드 생성
    wordcloud = WordCloud(font_path=font_path, width=800, height=400, background_color='white').generate_from_frequencies(keyword_counter)

    # 임시 파일로 저장
    with NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        wordcloud.to_file(tmp_file.name)
        tmp_file_path = tmp_file.name

    # S3에 파일 업로드
    s3_file_name = f"wordclouds/{user_id}/wordcloud_{user_id}.png"
    s3_client.upload_file(
        tmp_file_path,
        BUCKET_NAME,
        s3_file_name,
        ExtraArgs={"ACL": "public-read"}
    )

    # 로컬 임시 파일 삭제
    os.remove(tmp_file_path)

    # 업로드된 이미지 URL 반환
    image_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_file_name}"
    return image_url
