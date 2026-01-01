from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
from .models import Movie, DanhGia
from .models import Movie, DanhGia, LichSuXem
from django.db.models import Case, When

def get_recommendations_for_user(user, top_n=5):
    if not user.is_authenticated:
        return Movie.objects.order_by('-luot_xem')[:top_n]

    user_ratings = DanhGia.objects.filter(user=user)
    watched_history_ids = set(LichSuXem.objects.filter(user=user).values_list('phim_id', flat=True))
    liked_movie_ids = list(user_ratings.filter(diem__gte=3).values_list('phim_id', flat=True))
    if not liked_movie_ids:
        return Movie.objects.order_by('-luot_xem')[:top_n]

    movies = list(Movie.objects.prefetch_related('the_loai', 'dien_vien').all())

    movie_ids = []
    contents = []

    for m in movies:
        the_loai = " ".join([tl.ten.lower() for tl in m.the_loai.all()])
        dien_vien = " ".join([dv.ten.lower() for dv in m.dien_vien.all()])
        dao_dien = (m.dao_dien or "unknown").lower()
        mo_ta = (m.mo_ta or "").lower()

        content = f"{the_loai} {dao_dien} {dao_dien} {dao_dien} {dien_vien} {dien_vien} {dien_vien} {mo_ta}"
        contents.append(content)
        movie_ids.append(m.id)

    tfidf = TfidfVectorizer(stop_words='english', min_df=1, max_df=1.0)
    tfidf_matrix = tfidf.fit_transform(contents)

    df = pd.DataFrame({'movie_id': movie_ids, 'index': range(len(movie_ids))})
    liked_indices = df[df['movie_id'].isin(liked_movie_ids)]['index'].tolist()

    if not liked_indices:
        return Movie.objects.order_by('-luot_xem')[:top_n]

    sim_scores = np.zeros(tfidf_matrix.shape[0])
    for idx in liked_indices:
        sim_scores += cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()
    sim_scores /= len(liked_indices)

    liked_directors = set([m.dao_dien for m in movies if m.id in liked_movie_ids])
    bonus = [0.3 if m.dao_dien in liked_directors else 0 for m in movies]
    sim_scores += np.array(bonus)

    # Lấy các phim user đánh giá điểm thấp để loại bỏ
    disliked_ids = set(user_ratings.filter(diem__lt=3).values_list('phim_id', flat=True))
    # Lấy tất cả các phim user đã xem (đánh giá hoặc có trong lịch sử) để loại bỏ
    watched_movie_ids = set(user_ratings.values_list('phim_id', flat=True)) | watched_history_ids

    sim_df = pd.DataFrame({'movie_id': movie_ids, 'score': sim_scores})
    sim_df = sim_df[~sim_df['movie_id'].isin(disliked_ids)]  # Chỉ loại bỏ phim điểm thấp
    sim_df = sim_df[~sim_df['movie_id'].isin(watched_movie_ids)]
    sim_df = sim_df.sort_values(by='score', ascending=False)

    top_ids = sim_df.head(top_n)['movie_id'].tolist()
    return Movie.objects.filter(id__in=top_ids)
    
    # Sắp xếp QuerySet theo đúng thứ tự của top_ids
    preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(top_ids)])
    return Movie.objects.filter(id__in=top_ids).order_by(preserved_order)

# Hàm get_similar_movies giữ nguyên
def get_similar_movies(movie_id, top_n=5):
    movies = list(Movie.objects.prefetch_related('the_loai', 'dien_vien').all())

    movie_data = []
    for m in movies:
        the_loai = " ".join([tl.ten.lower() for tl in m.the_loai.all()])
        dien_vien = " ".join([dv.ten.lower() for dv in m.dien_vien.all()])
        dao_dien = (m.dao_dien or "unknown").lower()
        mo_ta = (m.mo_ta or "").lower()

        content = f"{the_loai} {dao_dien} {dao_dien} {dao_dien} {dien_vien} {dien_vien} {dien_vien} {mo_ta}"
        movie_data.append({'id': m.id, 'noi_dung': content})

    df = pd.DataFrame(movie_data)

    if movie_id not in df['id'].values:
        return Movie.objects.exclude(id=movie_id).order_by('-luot_xem')[:top_n]

    tfidf = TfidfVectorizer(stop_words='english', min_df=1, max_df=1.0)
    tfidf_matrix = tfidf.fit_transform(df['noi_dung'])

    index = df[df['id'] == movie_id].index[0]
    similarity_scores = cosine_similarity(tfidf_matrix[index], tfidf_matrix).flatten()

    df['similarity'] = similarity_scores
    df = df[df['id'] != movie_id]
    top_similar = df.sort_values(by='similarity', ascending=False).head(top_n)

    return Movie.objects.filter(id__in=top_similar['id'].tolist())
