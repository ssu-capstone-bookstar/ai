# from moto import mock_s3
# import boto3
# import pytest
# from wordcloud import WordCloud
# import os
# from tempfile import NamedTemporaryFile
# from io import BytesIO

# @mock_s3
# def test_create_wordcloud():
#     # 모의 S3 클라이언트 생성
#     s3_client = boto3.client(
#         "s3",
#         aws_access_key_id="test",
#         aws_secret_access_key="test",
#         region_name="ap-northeast-2"
#     )
    
#     # 모의 버킷 생성
#     s3_client.create_bucket(Bucket="database1")

#     # 임시 데이터와 워드클라우드 이미지 생성
#     user_id = "kelly"
#     keyword_data = {
#         "python": 5,
#         "fastapi": 3,
#         "s3": 2
#     }

#     # 워드 클라우드 생성
#     wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(keyword_data)
    
#     # 워드클라우드를 임시 파일로 저장
#     with NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
#         wordcloud.to_file(tmp_file.name)
#         tmp_file_path = tmp_file.name

#     # S3에 이미지 업로드
#     s3_file_name = f"wordclouds/{user_id}/wordcloud_{user_id}.png"
    
#     # 모의 S3에 업로드
#     s3_client.upload_file(
#         tmp_file_path,
#         "database1",
#         s3_file_name,
#         ExtraArgs={"ACL": "public-read"}
#     )

#     # S3에서 파일을 가져와 확인
#     response = s3_client.list_objects_v2(Bucket="database1", Prefix=f"wordclouds/{user_id}/")
#     assert 'Contents' in response
#     assert any(obj['Key'] == s3_file_name for obj in response['Contents'])

#     # 로컬 임시 파일 삭제
#     os.remove(tmp_file_path)

#     # S3 URL 생성 확인
#     image_url = f"https://{s3_client.meta.endpoint_url}/{s3_file_name}"
#     assert image_url == f"https://database1.s3.ap-northeast-2.amazonaws.com/wordclouds/{user_id}/wordcloud_{user_id}.png"


# #아래는 직접 이미지 넣어서 동작하는지 테스트하기 위함 
# import json
# import boto3
# from fastapi import FastAPI, File, UploadFile
# from io import BytesIO
# from PIL import Image
# from wordcloud import WordCloud
# from botocore.exceptions import ClientError
# from moto import mock_s3

# app = FastAPI()

# # S3 클라이언트 설정 및 버킷 생성
# @mock_s3
# def upload_wordcloud_to_s3(image_data: BytesIO, user_id: str):
#     # S3 클라이언트 생성
#     s3_client = boto3.client("s3", region_name="ap-northeast-2")
    
#     # 버킷 생성
#     s3_client.create_bucket(Bucket="database1", CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-2'})
    
#     # S3에 업로드할 파일 경로
#     s3_file_name = f"wordclouds/{user_id}/wordcloud_{user_id}.png"
    
#     # 이미지 S3 업로드
#     try:
#         s3_client.put_object(
#             Bucket="database1",
#             Key=s3_file_name,
#             Body=image_data,
#             ACL="public-read"  # 파일을 공용으로 읽을 수 있도록 설정
#         )
#         # S3 URL 반환
#         return f"https://database1.s3.ap-northeast-2.amazonaws.com/{s3_file_name}"
#     except ClientError as e:
#         # 업로드 실패 시 오류 반환
#         return str(e)

# # 워드 클라우드 생성 및 S3 업로드 API
# @app.post("/wordcloud")
# async def create_wordcloud(file: UploadFile = File(...), user_id: int):
#     # 업로드된 이미지를 읽어 BytesIO로 변환
#     image_data = await file.read()
#     image_data = BytesIO(image_data)
    
#     # 이미지를 PIL 객체로 변환하여 워드 클라우드 생성
#     try:
#         img = Image.open(image_data)
#         text = "여기에 워드 클라우드를 생성할 텍스트를 삽입"  # 예시 텍스트, 여기에 워드 클라우드를 생성할 텍스트 넣기
        
#         # 워드 클라우드 생성
#         wordcloud = WordCloud(width=800, height=800, background_color="white").generate(text)
        
#         # 워드 클라우드 이미지를 BytesIO로 저장
#         wordcloud_image = BytesIO()
#         wordcloud.to_image().save(wordcloud_image, format="PNG")
#         wordcloud_image.seek(0)  # 파일 포인터를 처음으로 이동
        
#         # S3에 업로드
#         image_url = upload_wordcloud_to_s3(wordcloud_image, user_id)
        
#         # S3 URL 반환
#         return {"wordcloud_image": image_url}
#     except Exception as e:
#         # 에러 발생 시 에러 메시지 반환
#         return {"error": str(e)}





import requests

# 서버 URL (FastAPI가 로컬에서 실행 중이라면 http://127.0.0.1:8000)
url = "https://t2.daumcdn.net/thumb/R720x0/?fname=http://t1.daumcdn.net/brunch/service/guest/image/wnKIOJBS3HbetFTd0JGLUCe3KNE.png"
#"http://127.0.0.1:8000/wordcloud_image/"

# 테스트할 이미지 URL과 user_id를 지정
image_url = "https://example.com/path/to/image.jpg"
user_id = 1  # 임의의 사용자 ID

# 요청에 보낼 데이터
data = {
    "user_id": user_id,
    "image_url": image_url
}

# POST 요청을 통해 서버에 데이터 보내기
response = requests.post(url, json=data)

# 응답 확인
if response.status_code == 200:
    result = response.json()
    print("워드 클라우드 URL:", result['wordcloud_url'])
else:
    print("에러 발생:", response.status_code, response.text)
