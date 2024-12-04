import boto3, os, re, requests, cv2, pytesseract, random
from collections import Counter
from wordcloud import WordCloud
from tempfile import NamedTemporaryFile
from sqlalchemy.orm import Session
import easyocr
from models import UserKeyword
from datetime import datetime
from io import BytesIO
import numpy as np
from easyocr import Reader 
from konlpy.tag import Okt
from nltk.util import ngrams
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from matplotlib import colors as mcolors
from dotenv import load_dotenv
load_dotenv()
okt = Okt()
BUCKET_NAME = os.getenv("BUCKET_NAME", "savewordcloud")

#pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe" #윈도우에서만 추가 필요 

s3_client = boto3.client(
    "s3"
)

ocr = easyocr.Reader(['ko'],gpu=False)
font_path = "/usr/share/fonts/truetype/myfonts/myfont.ttf" #"C:\\Users\\kelly\\Documents\\AI\\nanum-all\\NanumGothic.ttf" 
stopwords = {"은", "는", "이", "가", "의", "에", "을", "에서", "도", "로", "으로", "와", "과", 
             "한", "하다", "들", "위한", "으로부터", "라도", "하고", "그리고", "때문에", "하지만","싶다","달리","어단","어름","않는","않은"}

def preprocess_text(text):
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣]', '', text)
    tokens = okt.pos(text, norm=False, stem=False)
    print("Tokens:", tokens)  # 분석된 토큰 확인

    allowed_pos = {"Noun", "Verb", "Adjective"}
    filtered_words = [word for word, pos in tokens if pos in allowed_pos]
    
    meaningful_words = [word for word in filtered_words if word not in stopwords or (word in stopwords and 'Adjective' in [pos for _, pos in tokens if _ == word])]
    
    incorrect_words = {"교대": "그대로","대하":"대하는","뚜정":"투정"}
    meaningful_words = [incorrect_words.get(word,word) for word in meaningful_words]
    
    print("meaningful_words:", meaningful_words)
    bigrams = generate_ngrams(" ".join(meaningful_words), n=2)
    trigrams = generate_ngrams(" ".join(meaningful_words), n=3)
    
    return meaningful_words + bigrams + trigrams

def preprocess_image(image_np):
    gray_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
    binary_image = cv2.adaptiveThreshold(
        blurred_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    contrast_image = cv2.convertScaleAbs(binary_image, alpha=1.5, beta=0)
    return contrast_image
    # return binary_image

def generate_ngrams(text, n=2):
    tokens = text.split()
    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngram = tokens[i:i + n]
        if all(word not in stopwords for word in ngram):
            ngrams.append(" ".join(ngram))
    return ngrams

def resize_image(image, scale=2.0):
    height, width = image.shape[:2]
    return cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_LINEAR)


def correct_image_orientation(image):
    coords = cv2.findNonZero(cv2.bitwise_not(image))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated


def extract_keywords(image_url: str) -> List[str]:
    response = requests.get(image_url)
    image_bytes = BytesIO(response.content)
    image_np = np.frombuffer(image_bytes.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    
    image = preprocess_image(image)
    image = resize_image(image, scale=2.0)
    image = correct_image_orientation(image)

    ocr = Reader(['ko'])  #우선 한글
    ocr_results = ocr.readtext(image, detail=1, paragraph=True) #이거는 easyocr일 경우
    full_text = pytesseract.image_to_string(image, lang="kor",config="==psm 6")
    extracted_text = []
    for result in ocr_results:
        if len(result) >= 2: 
            text = result[1]
            confidence = result[2] if len(result) > 2 else None 
            if confidence is None or confidence > 0.7: 
                extracted_text.append(text)
    if full_text:
        extracted_text.append(full_text)
    full_text = " ".join(extracted_text)

    print("Full Text:", full_text)
    
    processed_text = preprocess_text(full_text)
    if not processed_text:
        return 0
    
    print("processed_text: ", processed_text)
    keywords = filter_keywords(processed_text)
    
    print("Keywords:", keywords)
    return keywords

def filter_keywords(text: str) -> List[str]:
    """TF-IDF를 기반으로 중요한 키워드 추출."""
    if isinstance(text, list):
        text = " ".join(text)
    tfidf_vectorizer = TfidfVectorizer(
        max_features=15,  #상위 몇개의 키워드로!
        stop_words="english",
        ngram_range=(1, 1) #단어만 취급하도록! 
    )
    tfidf_matrix = tfidf_vectorizer.fit_transform([text])
    feature_names = tfidf_vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray().flatten()

    keyword_scores = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
    filtered_keywords = [kw for kw, score in keyword_scores if score > 0.15 and len(kw) > 1]

    return filtered_keywords

def update_user_keywords(user_id: int, keywords: list, db: Session):
    keyword_counts = Counter(keywords)
    for keyword, count in keyword_counts.items():
        db_keyword = db.query(UserKeyword).filter_by(user_id=user_id, keyword=keyword).first()
        if db_keyword:
            db_keyword.frequency += count
        else:
            db.add(UserKeyword(user_id=user_id, keyword=keyword, frequency=count))
    db.commit()


def create_wordcloud(user_id: int, db: Session):
    keyword_data = db.query(UserKeyword).filter_by(user_id=user_id).all()
    keyword_counter = Counter({kw.keyword: kw.frequency for kw in keyword_data})
    
    wordcloud = WordCloud(font_path=font_path, width=800, height=400, background_color='white', color_func=random_named_color_func).generate_from_frequencies(keyword_counter)

    with NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        wordcloud.to_file(tmp_file.name)
        tmp_file_path = tmp_file.name

    s3_file_name = f"wordclouds/{user_id}/wordcloud_{user_id}.png"
    s3_client.upload_file(
        tmp_file_path,
        BUCKET_NAME,
        s3_file_name
    )

    os.remove(tmp_file_path)
    image_url = generate_presigned_url(BUCKET_NAME, s3_file_name)
    return image_url

def generate_presigned_url(bucket_name, object_key, expiration=3600):
    try:
        url = s3_client.generate_presigned_url('get_object',
                                               Params={'Bucket': bucket_name, 'Key': object_key},
                                               ExpiresIn=expiration)
        return url
    except Exception as e:
        return str(e)

def random_named_color_func(*args, **kwargs):
    named_colors = list(mcolors.CSS4_COLORS.values())  # HTML/CSS 기반 색상
    return random.choice(named_colors)  # 랜덤 색상 

def object_exists(bucket_name, object_key):
    try:
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        return True
    except s3_client.exceptions.ClientError:
        return False