from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import random
import numpy as np
from typing import Dict
from collections import defaultdict
import torch
import torch.nn as nn
from sklearn.neighbors import NearestNeighbors
import logging
from models import Book, Member, MemberBook, ReadingStatus, BookCategory, RecommenderModel
def create_user_item_matrix(db: Session, user_id: int):
    users_books = db.query(Member.id, MemberBook.book_id).join(MemberBook, Member.id == MemberBook.member_id).all()
    user_data = {}
    for uid, book_id in users_books:
        user_data.setdefault(uid, set()).add(book_id)
    
    all_books = list(set(book_id for books in user_data.values() for book_id in books))
    user_ids = list(user_data.keys())
    user_item_matrix = np.zeros((len(user_ids), len(all_books)))
    
    for uid_index, uid in enumerate(user_ids):
        for book_id in user_data[uid]:
            user_item_matrix[uid_index, all_books.index(book_id)] = 1
    logging.info(f"User-Item Matrix Shape: {user_item_matrix.shape}")
    
    return user_item_matrix, user_ids, all_books

def train_model(user_item_matrix, num_epochs=300, learning_rate=0.122):
    user_item_tensor = torch.FloatTensor(user_item_matrix)
    model = RecommenderModel(user_item_tensor.shape[1])
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    for epoch in range(num_epochs):
        model.train()
        optimizer.zero_grad()
        outputs = model(user_item_tensor)
        loss = criterion(outputs, user_item_tensor)
        loss.backward()
        optimizer.step()
        
        if epoch % 100 == 0:
            logging.info(f'Epoch [{epoch}/{num_epochs}], Loss: {loss.item():.4f}')
    
    return model

def recommend_with_pytorch(model, user_id_index, all_books, top_n=5):
    with torch.no_grad():
        user_tensor = torch.FloatTensor(np.zeros((1, model.fc1.in_features)))
        user_tensor[0, user_id_index] = 1
        predictions = model(user_tensor).numpy().flatten()
    
    recommended_indices = predictions.argsort()[-top_n:][::-1]
    return [all_books[i] for i in recommended_indices]


def calculate_author_weight(author, books, read_list, want_list):
    preferred_authors = []
    for book in books:
        if book.book_id in read_list + want_list:
            preferred_authors.append(book.author)
    preferred_authors_set = set([author for author in preferred_authors if preferred_authors.count(author) > 1])

    if author in preferred_authors_set:
        return 2.5 
    return 0 

def calculate_category_weight(book_category: str, total_categories: Dict[str, float]) -> float:
    weight = total_categories.get(book_category, 0)  
    return weight

def get_user_preference_categories(db: Session, book_ids: List[str]) -> Dict[str, float]:
    category_scores = defaultdict(int)  

    for book_id in book_ids:
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            category = book.book_category 
            if category:
                category_scores[category] += 2  
            else:
                logging.warning(f"Book with ID {book_id} has no category.")
        else:
            logging.warning(f"Book with ID {book_id} not found.")

    logging.info(f"User preference categories: {category_scores}")  # 확인
    return category_scores


def get_similar_users(db: Session, read_list: List[str], user_id: int, num_similar_users=4):
    users_books = db.query(Member.id, MemberBook.book_id).join(MemberBook, Member.id == MemberBook.member_id).all()
    user_data = {uid: set() for uid, _ in users_books}
    for uid, book_id in users_books:
        user_data[uid].add(book_id)

    if user_id not in user_data:
        return []

    all_books = list(set(book_id for books in user_data.values() for book_id in books))
    user_ids = list(user_data.keys())
    feature_matrix = [[1 if book in user_data[uid] else 0 for book in all_books] for uid in user_ids]

    knn = NearestNeighbors(n_neighbors=num_similar_users)
    knn.fit(feature_matrix)
    current_user_index = user_ids.index(user_id)
    distances, indices = knn.kneighbors([feature_matrix[current_user_index]])

    return [user_ids[idx] for idx in indices.flatten() if idx != current_user_index][:num_similar_users]


def recommend_books(db: Session, user_id: int, read_list: List[str], want_list: List[str], num_recommendations):
    books = db.query(Book).all()
    if not books:
        logging.error("No books found in the database.")
        return []
    
    df = pd.DataFrame([{"book_id": book.book_id, "title": book.title, "author": book.author, "book_category": book.book_category} for book in books])
    

    if not read_list and not want_list:
        random_books = random.sample(range(len(df)), min(num_recommendations, len(df)))
        return df.iloc[random_books][["book_id", 'title', 'author', 'book_category']].to_dict(orient='records')

    read_categories = get_user_preference_categories(db, read_list)
    want_categories = get_user_preference_categories(db, want_list)

    total_categories = defaultdict(float, read_categories) 
    for category, score in want_categories.items():
        total_categories[category] += score 
    
    logging.info(f"Total categories after merging read and want categories: {total_categories}")

    # 유사 사용자 기반 추천 책 선택
    similar_users = get_similar_users(db, read_list, user_id)
    potential_recommendations = set()
    if similar_users:
        for uid in similar_users:
            user_books = db.query(MemberBook.book_id).filter(MemberBook.member_id == uid).all()
            potential_recommendations.update([book[0] for book in user_books])
        potential_recommendations -= set(read_list) | set(want_list)

    logging.info(f"Potential recommendations (based on similar users): {potential_recommendations}")

    # 카테고리와 저자 가중치 계산
    df['weight'] = df['book_category'].apply(lambda x: calculate_category_weight(x, total_categories) if pd.notna(x) else 0)
    df['author_weight'] = df['author'].apply(lambda x: calculate_author_weight(x, books, read_list, want_list))
    logging.info(f"Author weights: {df[['author', 'author_weight']]}")
    df['total_weight'] = df['weight'] + df['author_weight']

    logging.info(f"Author weights: {df[['author', 'author_weight']].head()}")
    logging.info(f"Total weights: {df[['book_id', 'title', 'total_weight']].nlargest(5, 'total_weight')}")

    # 잠재 추천 책 DataFrame 생성, 상위 권수 선택
    if potential_recommendations:
        df_potential = df[df['book_id'].isin(potential_recommendations)]
        recommend_titles = pd.concat([df_potential, df.nlargest(num_recommendations, 'total_weight')]).drop_duplicates()
    else:
        recommend_titles = df.nlargest(num_recommendations, 'total_weight')

    # PyTorch 추천 책과 결합
    user_item_matrix, user_ids, all_books = create_user_item_matrix(db, user_id)
    model = train_model(user_item_matrix)
    user_id_index = user_ids.index(user_id)
    pytorch_recommendations = recommend_with_pytorch(model, user_id_index, all_books, top_n=num_recommendations)
    
    pytorch_recommendations_df = df[df['book_id'].isin(pytorch_recommendations)]
    final_recommendations = pd.concat([recommend_titles, pytorch_recommendations_df]).drop_duplicates()

   
    final_recommendations = final_recommendations[~final_recommendations['book_id'].isin(read_list)].head(num_recommendations)

    if len(final_recommendations) < num_recommendations:
        remaining_books = df[~df['book_id'].isin(final_recommendations['book_id']) & ~df['book_id'].isin(read_list)]
        additional_titles = remaining_books.sample(n=num_recommendations - len(final_recommendations), random_state=1)
        final_recommendations = pd.concat([final_recommendations, additional_titles])

    # 최종 추천 
    final_recommendations = final_recommendations.head(num_recommendations)
    return final_recommendations[['book_id', 'title', 'author', 'book_category']].to_dict(orient='records')
