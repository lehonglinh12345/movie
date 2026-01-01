from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .recommendations import get_recommendations_for_user

from django.db.models import Avg

from .models import Movie, User, TheLoai, LichSuXem

# Trang chủ và giới thiệu
from django.db.models import Count
from django.shortcuts import render
from .models import Movie
import requests


def lay_trailer_tmdb(movie_id):
    API_KEY = 'c53ff05a507beb95ce9c55f89908d88d'
    url = f'https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}&language=vi-VN'
    response = requests.get(url)
    data = response.json()

    for video in data.get('results', []):
        if video['site'] == 'YouTube' and video['type'] == 'Trailer':
            return f"https://www.youtube.com/embed/{video['key']}"
    return None

from .models import Movie, TheLoai , DanhGia  # đảm bảo bạn đã import đúng model
from django.db.models import Avg
from django.utils.timezone import now
from django.db.models import Q, Avg
from django.db.models.functions import ExtractYear
from .models import Movie, TheLoai

def home(request):
    today = now().date()

    # Tự động cập nhật trạng thái
    Movie.objects.filter(
        Q(trang_thai='sap_chieu') & Q(ngay_phat_hanh__lte=today)
    ).update(trang_thai='dang_chieu')

    # Bộ lọc
    genre_id = request.GET.get('genre')
    year = request.GET.get('year')
    status = request.GET.get('status')

    movie_filter = Q()
    if genre_id:
        movie_filter &= Q(the_loai__id=genre_id)
    if year:
        movie_filter &= Q(ngay_phat_hanh__year=year)
    if status:
        movie_filter &= Q(trang_thai=status)

    # Danh sách phim theo bộ lọc
    danh_sach_phim = Movie.objects.filter(movie_filter).annotate(
        danh_gia=Avg('reviews__diem')
    ).distinct().order_by('-ngay_phat_hanh')[:20]

    # Các danh sách khác
    phim_moi_nhat = Movie.objects.annotate(danh_gia=Avg('reviews__diem')).order_by('-ngay_phat_hanh')[:10]
    phim_yeu_thich = Movie.objects.annotate(danh_gia=Avg('reviews__diem')).order_by('-ngay_phat_hanh')[:5]
    phim_hay_nhat = Movie.objects.annotate(danh_gia=Avg('reviews__diem')).order_by('-luot_xem')[:5]
    phim_dang_chieu = Movie.objects.filter(trang_thai='dang_chieu').annotate(danh_gia=Avg('reviews__diem'))[:10]
    phim_sap_chieu = Movie.objects.filter(trang_thai='sap_chieu').annotate(danh_gia=Avg('reviews__diem'))[:10]

    # Gợi ý phim
    recommended = get_recommendations_for_user(request.user)
    for movie in recommended:
        movie.avg_score = movie.reviews.aggregate(avg=Avg('diem'))['avg'] or 0

    # Dữ liệu cho filter
    all_genres = TheLoai.objects.all()
    all_years = Movie.objects.annotate(
        year=ExtractYear('ngay_phat_hanh')
    ).values('year').distinct().order_by('-year')

    has_filter = bool(genre_id or year or status)

    context = {
        'has_filter': has_filter,
        'phim_moi_nhat': phim_moi_nhat,
        'danh_sach_phim': danh_sach_phim,
        'phim_noi_bat': danh_sach_phim[:3],
        'phim_yeu_thich': phim_yeu_thich,
        'phim_hay_nhat': phim_hay_nhat,
        'phim_dang_chieu': phim_dang_chieu,
        'phim_sap_chieu': phim_sap_chieu,
        'recommended_movies': recommended,
        'all_genres': all_genres,
        'all_years': all_years,
    }

    return render(request, 'myapp/pages/home.html', context)




from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Movie


def dieukhoan(request):
    return render(request, "myapp/quydinh/dieukhoan.html")
def quyen(request):
    return render(request, "myapp/quydinh/quyen.html")
def gioithieu(request):
    return render(request, 'myapp/quydinh/gioithieu.html')

def home1(request):
    return render(request, "myapp/pages/home1.html")

# Chi tiết phim
def onepiece(request):
    movie = get_object_or_404(Movie, ten_phim="One Piece") 
    return render(request, 'myapp/pages/phim/onepiece.html', {'movie': movie})

def kime(request):
    movie = get_object_or_404(Movie, ten_phim="Kimetsu no Yaiba") 
    return render(request, 'myapp/pages/phim/kime.html', {'movie': movie})

def natra(request):
    movie = get_object_or_404(Movie, ten_phim="NaTra2") 
    return render(request, 'myapp/pages/phim/natra.html', {'movie': movie})


from django.shortcuts import render, get_object_or_404
from .models import Movie
from django.utils.timezone import now
from .models import Movie, LichSuXem
from itertools import chain
from django.db.models import Avg


@login_required



def chitietphim(request, maphim):
    movie = get_object_or_404(Movie, maphim=maphim)

    by_genre = Movie.objects.filter(the_loai__in=movie.the_loai.all()).exclude(id=movie.id)
    by_director = Movie.objects.filter(dao_dien=movie.dao_dien).exclude(id=movie.id)

    dien_vien_ids = movie.dien_vien.values_list('id', flat=True)
    by_actor = Movie.objects.filter(dien_vien__id__in=dien_vien_ids).exclude(id=movie.id)

    combined = list({m.id: m for m in chain(by_genre, by_director, by_actor)}.values())
    combined = sorted(combined, key=lambda m: m.ngay_phat_hanh or now().date(), reverse=True)

    recommended_movies = get_similar_movies(movie.id, top_n=6)

    # Tính điểm đánh giá trung bình cho phim chi tiết
    movie.avg_score = movie.reviews.aggregate(avg=Avg('diem'))['avg'] or 0

    # Tính điểm đánh giá trung bình cho các phim gợi ý
    for m in recommended_movies:
        m.avg_score = m.reviews.aggregate(avg=Avg('diem'))['avg'] or 0

    lich_su, created = LichSuXem.objects.get_or_create(
        user=request.user,
        phim=movie,
        defaults={'thoi_gian_bat_dau': now()}
    )
    if not created:
        lich_su.thoi_gian_bat_dau = now()
        lich_su.save()

    movie.update_luot_xem()

    today = now().date()
    phim_duoc_xem = movie.ngay_phat_hanh and movie.ngay_phat_hanh <= today

    if phim_duoc_xem and movie.video_url:
        video_embed = get_video_embed_url(movie.video_url)
    elif movie.trailer_url:
        video_embed = get_video_embed_url(movie.trailer_url)
    else:
        video_embed = None

    return render(request, 'myapp/pages/chitietphim.html', {
        'movie': movie,
        'recommended_movies': recommended_movies,
        'video_embed': video_embed,
        'phim_duoc_xem': phim_duoc_xem,
    })



# Chức năng đăng nhập
def login_view(request):   
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')  # xử lý next từ form hoặc URL

        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect(next_url if next_url else 'home')
        else:
            messages.error(request, 'Email hoặc mật khẩu không đúng!')
            return render(request, 'myapp/log/login.html', {
                'email': email,
                'next': next_url  # truyền lại vào template
            })

    # GET request
    return render(request, 'myapp/log/login.html', {
        'next': request.GET.get('next', '')
    })

from django.template.defaulttags import register

@register.filter
def filter_by_id(queryset, id):
    return queryset.get(id=id).ten if queryset.filter(id=id).exists() else ''
@csrf_exempt
def profile(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return render(request, 'myapp/log/login.html')
        return render(request, "myapp/log/profile.html")
    if not request.user.is_authenticated:
        return render(request, 'myapp/log/login.html')
    return render(request, "myapp/log/profile.html")

# Chức năng tìm kiếm phim
def search_movies(request):
    query = request.GET.get("q", "").strip()
    genre = request.GET.get("genre", "").strip()
    movies = Movie.objects.all()

    if query:
        movies = movies.filter(ten_phim__icontains=query)
    if genre:
        movies = movies.filter(the_loai__ten__icontains=genre)

    return render(request, "myapp/search/search_results.html", {"movies": movies.distinct(), "query": query, "genre": genre})
from django.contrib.auth.decorators import login_required

@login_required
def xem_phim(request, id):
    movie = get_object_or_404(Movie, id=id)
    return render(request, 'myapp/xem_phim.html', {'movie': movie})



@login_required
def lich_su_xem(request):
    lich_su = LichSuXem.objects.filter(user=request.user).select_related('phim').order_by('-thoi_gian_bat_dau')
    return render(request, 'myapp/pages/lich_su_xem.html', {'lich_su': lich_su})
# Cập nhật thông tin cá nhân
@csrf_exempt
@login_required
def update_fullname(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_fullname = data.get("fullname")
            user = request.user
            user.fullname = new_fullname
            user.save()
            return JsonResponse({"success": True, "fullname": new_fullname})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})





from django.shortcuts import render, get_object_or_404
from .models import TheLoai, Movie

def the_loai(request, ten):
    the_loai = get_object_or_404(TheLoai, ten=ten)
    movies = Movie.objects.filter(the_loai=the_loai)
    return render(request, 'myapp/pages/the_loai.html', {'the_loai': the_loai, 'movies': movies})







import re

def get_video_embed_url(url):
    if not url:
        return None
    
    # Kiểm tra nếu URL là YouTube URL chuẩn (watch?v=)
    if "watch?v=" in url:
        video_id = url.split("watch?v=")[-1].split("&")[0]  # Lấy phần ID và loại bỏ các tham số phụ
        return f"https://www.youtube.com/embed/{video_id}"
    
    # Kiểm tra nếu URL là YouTube URL dạng rút gọn (youtu.be/)
    elif "youtu.be/" in url:
        video_id = url.split("/")[-1].split("?")[0]  # Tách ID video và loại bỏ các tham số
        # Kiểm tra nếu video ID hợp lệ (chỉ chứa ký tự hợp lệ của YouTube)
        if re.match(r'^[A-Za-z0-9_-]+$', video_id):
            return f"https://www.youtube.com/embed/{video_id}"
        else:
            return None  # Nếu ID không hợp lệ thì trả về None
    
    # Nếu không phải URL YouTube hợp lệ
    return None


from .models import TheLoai

def danh_sach_the_loai(request):
    return {'categories': TheLoai.objects.all()}


# myapp/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import User

# @login_required
# def profile(request):
#     user = request.user
#     if request.method == 'POST' and 'avatar' in request.FILES:
#         user.avatar = request.FILES['avatar']
#         user.save()
#         return JsonResponse({'success': True, 'avatar_url': user.avatar.url})
#     return render(request, 'myapp/log/profile.html', {'user': user})
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

@csrf_exempt
@login_required
def update_avatar(request):
    if request.method == 'POST':
        try:
            avatar = request.FILES.get('avatar')
            if not avatar:
                return JsonResponse({'success': False, 'error': 'Không tìm thấy file ảnh'})

            user = request.user
            user.avatar = avatar
            user.save()
            return JsonResponse({'success': True, 'avatar_url': user.avatar.url})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Yêu cầu không hợp lệ'})



def phim_sap_chieu(request):
    upcoming_movies = Movie.objects.filter(trang_thai='Sắp Chiếu')  

    # 🛠 In log để kiểm tra dữ liệu
    print("🔥 DEBUG: Số lượng phim sắp chiếu:", upcoming_movies.count())
    for movie in upcoming_movies:
        print(f"🎬 {movie.ten_phim} - {movie.trang_thai}")

    context = {'upcoming_movies': upcoming_movies}
    return render(request, 'myapp/pages/home1.html', context)


from django.shortcuts import render
from .models import Movie

def upcoming_movies(request):
    # Lọc phim có trạng thái "Sắp Chiếu"
    movies = Movie.objects.filter(trang_thai="sap_chieu").order_by('ngay_phat_hanh')
    
    return render(request, 'phim/home1.html', {'movies': movies})


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    the_loai_list = movie.the_loai.all()  # Lấy tất cả thể loại của phim này
    similar_movies = Movie.objects.filter(the_loai__in=the_loai_list).exclude(id=movie.id).distinct()[:5]
    
    return render(request, 'myapp/pages/phim/movie_detail.html', {
        'movie': movie,
        'similar_movies': similar_movies,
    })
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Movie, DanhGia
from django.http import HttpResponseForbidden
from django.utils import timezone 

@login_required
def movie_review(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    if request.method == "POST":
        diem = request.POST.get('diem')
        binh_luan = request.POST.get('binh_luan')
        try:
            diem = float(diem)
            if not (0 <= diem <= 5):  # khớp với model
                messages.error(request, "Điểm đánh giá phải từ 0 đến 5.")
                return redirect('chitietphim', maphim=movie.maphim)
        except (ValueError, TypeError):
            messages.error(request, "Điểm đánh giá không hợp lệ.")
            return redirect('chitietphim', maphim=movie.maphim)

        if not binh_luan:
            messages.error(request, "Bình luận không được để trống.")
            return redirect('chitietphim', maphim=movie.maphim)

        danh_gia = DanhGia.objects.filter(user=request.user, phim=movie).first()
        if danh_gia:
            danh_gia.diem = diem
            danh_gia.binh_luan = binh_luan
            danh_gia.ngay_danh_gia = timezone.now()
            danh_gia.save()
        else:
            DanhGia.objects.create(user=request.user, phim=movie, diem=diem, binh_luan=binh_luan, ngay_danh_gia=timezone.now())

        messages.success(request, "Đánh giá của bạn đã được lưu!")
        return redirect('chitietphim', maphim=movie.maphim)
    return redirect('chitietphim', maphim=movie.maphim)




from django.shortcuts import render, get_object_or_404
from .models import Movie
from .recommendations import get_recommendations_for_user, get_similar_movies

def recommended_movies_view(request):
    user = request.user
    if user.is_authenticated:
        recommended_movies = get_recommendations_for_user(user, top_n=5)
    else:
        recommended_movies = Movie.objects.order_by('-ngay_phat_hanh')[:5]

    return render(request, 'myapp/pages/recommended.html', {
        'recommended_movies': recommended_movies
    })

def movie_detail_view(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    similar_movies = get_similar_movies(movie_id, top_n=5)

    return render(request, 'myapp/pages/movie_detail.html', {
        'movie': movie,
        'similar_movies': similar_movies
    })

def recommend_movies(request):
    recommended_movies = []
    message = ""

    if request.user.is_authenticated:

        recommended_movies = get_recommendations_for_user(request.user.id, top_n=3)
        message = "Phim gợi ý cho bạn:" if recommended_movies.exists() else "Chưa có gợi ý, xem phim phổ biến:"
    else:
        recommended_movies = Movie.objects.order_by('-ngay_phat_hanh')[:5]
        message = "Đăng nhập để nhận gợi ý cá nhân hóa:"

    return render(request, 'myapp/recommended.html', {
        'recommended_movies': recommended_movies,
        'message': message,
    })



# from .recommendations import get_recommendations_for_user

# from django.shortcuts import render
# from .models import Movie, DanhGia

# import pandas as pd
# from sklearn.metrics.pairwise import cosine_similarity
# from functools import lru_cache
# from .models import DanhGia, Movie

# from django.db.models import Count
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# import numpy as np
# import pandas as pd

# def get_recommendations_for_user(user, limit=5):
#     from .models import Movie, DanhGia

#     if not user.is_authenticated:
#         return Movie.objects.order_by('-luot_xem')[:limit]

#     user_ratings = DanhGia.objects.filter(user=user)
#     if not user_ratings.exists():
#         return Movie.objects.order_by('-luot_xem')[:limit]

#     liked_movie_ids = list(user_ratings.filter(diem__gte=3).values_list('phim_id', flat=True))
#     if not liked_movie_ids:
#         return Movie.objects.order_by('-luot_xem')[:limit]

#     # Lấy toàn bộ phim với prefetch
#     movies = list(Movie.objects.prefetch_related('the_loai', 'dien_vien').all())
#     movie_ids = []
#     contents = []

#     for m in movies:
#         the_loai_names = " ".join([tl.ten.lower() for tl in m.the_loai.all()])
#         dien_vien_names = " ".join([dv.ten.lower() for dv in m.dien_vien.all()])
#         dao_dien = (m.dao_dien or "unknown").lower()
#         mo_ta = (m.mo_ta or "").lower()

#         # Lặp lại đạo diễn & diễn viên 3 lần để tăng trọng số
#         content = f"{the_loai_names} {dao_dien} {dao_dien} {dao_dien} {dien_vien_names} {dien_vien_names} {dien_vien_names} {mo_ta}"
#         contents.append(content)
#         movie_ids.append(m.id)

#     # TF-IDF vectorizer: giữ cả từ hiếm
#     tfidf = TfidfVectorizer(stop_words='english', min_df=1, max_df=1.0)
#     tfidf_matrix = tfidf.fit_transform(contents)

#     # Tìm chỉ số phim user đã thích
#     df = pd.DataFrame({'movie_id': movie_ids, 'index': range(len(movie_ids))})
#     liked_indices = df[df['movie_id'].isin(liked_movie_ids)]['index'].tolist()
#     if not liked_indices:
#         return Movie.objects.order_by('-luot_xem')[:limit]

#     # Tính cosine similarity trung bình giữa phim đã thích và tất cả
#     sim_scores = np.zeros(tfidf_matrix.shape[0])
#     for idx in liked_indices:
#         sim_scores += cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()
#     sim_scores /= len(liked_indices)

#     # Tính điểm bonus nếu trùng đạo diễn
#     liked_directors = set([m.dao_dien for m in movies if m.id in liked_movie_ids])
#     bonus = [0.3 if m.dao_dien in liked_directors else 0 for m in movies]
#     sim_scores += np.array(bonus)

#     # Loại bỏ phim đã xem
#     watched_movie_ids = set(user_ratings.values_list('phim_id', flat=True))
#     sim_df = pd.DataFrame({'movie_id': movie_ids, 'score': sim_scores})
#     sim_df = sim_df[~sim_df['movie_id'].isin(watched_movie_ids)]
#     sim_df = sim_df.sort_values(by='score', ascending=False)

#     # Lấy top N
#     recommended_ids = sim_df.head(limit)['movie_id'].tolist()
#     return Movie.objects.filter(id__in=recommended_ids)








from django.http import JsonResponse
from django.core import serializers

def load_reviews(request, movie_id):
    page = int(request.GET.get('page', 1))
    per_page = 5
    start = (page - 1) * per_page
    end = start + per_page

    reviews = DanhGia.objects.filter(phim_id=movie_id).order_by('-ngay_danh_gia')[start:end]

    data = []
    for review in reviews:
        data.append({
            'username': review.user.get_full_name() or review.user.email,
            'is_owner': review.user == request.user,
            'avatar': review.user.avatar.url if review.user.avatar else '/static/myapp/img/default_avatar.jpg',
            'ngay_danh_gia': review.ngay_danh_gia.strftime("%d/%m/%Y %H:%M"),
            'diem': review.diem,
            'binh_luan': review.binh_luan,
        })

    return JsonResponse({'reviews': data, 'has_more': DanhGia.objects.filter(phim_id=movie_id).count() > end})


@login_required
def toggle_favorite(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            movie_id = data.get('movie_id')
            movie = get_object_or_404(Movie, id=movie_id)
            user = request.user
            if movie in user.favorites.all():
                user.favorites.remove(movie)
                is_favorite = False
            else:
                user.favorites.add(movie)
                is_favorite = True
            return JsonResponse({'success': True, 'is_favorite': is_favorite})
        except Movie.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Phim không tồn tại'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import DanhGia

@login_required
@require_POST
def edit_review(request):
    import json
    data = json.loads(request.body)
    review_id = data.get('review_id')
    diem = data.get('diem')
    binh_luan = data.get('binh_luan')

    try:
        review = DanhGia.objects.get(id=review_id, user=request.user)
        review.diem = diem
        review.binh_luan = binh_luan
        review.save()
        return JsonResponse({'success': True, 'diem': diem, 'binh_luan': binh_luan})
    except DanhGia.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy bình luận hoặc không có quyền sửa.'})

@login_required
@require_POST
def delete_review(request):
    import json
    data = json.loads(request.body)
    review_id = data.get('review_id')

    try:
        review = DanhGia.objects.get(id=review_id, user=request.user)
        review.delete()
        return JsonResponse({'success': True})
    except DanhGia.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy bình luận hoặc không có quyền xóa.'})




















from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, TheLoai
from .forms import MovieForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from .forms import MovieForm
from .models import Movie
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models import Count, Avg
from django.utils.timezone import now
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models.functions import TruncMonth
from .models import Movie, DanhGia, LichSuXem, User
from django.shortcuts import render
from django.db.models import Count, Avg, Sum
from django.db.models.functions import TruncMonth
from .models import Movie, User, TheLoai, DanhGia, LichSuXem, DienVien

from django.shortcuts import render
from django.db.models import Count, Avg, Sum
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth

from .models import Movie, User, TheLoai, DanhGia, LichSuXem, DienVien


User = get_user_model()


from django.db.models import Q  # Nhớ import nếu muốn mở rộng điều kiện tìm kiếm

from django.db.models import Q

def admin_dashboard(request):
    User = get_user_model()

    # --- Tìm kiếm phim ---
    movie_query = request.GET.get("q", "")
    movie_list = Movie.objects.all().order_by('id')
    if movie_query:
        movie_list = movie_list.filter(ten_phim__icontains=movie_query)

    # --- Tìm kiếm đánh giá ---
    review_query = request.GET.get("review_q", "")
    danh_gia_list = DanhGia.objects.select_related('user', 'phim').all().order_by('id')
    if review_query:
        danh_gia_list = danh_gia_list.filter(
            Q(user__email__icontains=review_query) |
            Q(phim__ten_phim__icontains=review_query)
        )

    # --- Các danh sách khác ---
    user_list = User.objects.all().order_by('id')
    genre_list = TheLoai.objects.all().order_by('id')
    actor_list = DienVien.objects.all().order_by('id')

    # --- Phân trang ---
    movie_paginator = Paginator(movie_list, 5)
    user_paginator = Paginator(user_list, 5)
    genre_paginator = Paginator(genre_list, 5)
    actor_paginator = Paginator(actor_list, 5)
    danh_gia_paginator = Paginator(danh_gia_list, 5)

    movie_page_number = request.GET.get('movie_page')
    user_page_number = request.GET.get('user_page')
    genre_page_number = request.GET.get('genre_page')
    actor_page_number = request.GET.get('actor_page')
    danh_gia_page_number = request.GET.get('review_page')

    movies = movie_paginator.get_page(movie_page_number)
    users = user_paginator.get_page(user_page_number)
    genres = genre_paginator.get_page(genre_page_number)
    actors = actor_paginator.get_page(actor_page_number)
    danh_gia = danh_gia_paginator.get_page(danh_gia_page_number)

    # --- Thống kê ---
    tong_nguoi_dung = user_list.count()
    tong_phim = movie_list.count()
    tong_danh_gia = danh_gia_list.count()
    tong_luot_xem = movie_list.aggregate(total=Sum('luot_xem'))['total'] or 0

    top_phim_xem = movie_list.order_by('-luot_xem')[:5]
    top_phim_danh_gia = movie_list.annotate(avg_diem=Avg('reviews__diem')).order_by('-avg_diem')[:5]
    top_user = user_list.annotate(luot_xem=Count('watch_history')).order_by('-luot_xem').first()

    xem_theo_thang = (
        LichSuXem.objects.annotate(thang=TruncMonth('thoi_gian_bat_dau'))
        .values('thang')
        .annotate(count=Count('id'))
        .order_by('thang')
    )

    danh_gia_theo_thang = (
        DanhGia.objects.annotate(thang=TruncMonth('ngay_danh_gia'))
        .values('thang')
        .annotate(count=Count('id'))
        .order_by('thang')
    )
    stats = [
        {'icon': '👤', 'title': 'Người dùng', 'value': tong_nguoi_dung},
        {'icon': '🎬', 'title': 'Tổng phim', 'value': tong_phim},
        {'icon': '⭐', 'title': 'Lượt đánh giá', 'value': tong_danh_gia},
        {'icon': '👁️‍🗨️', 'title': 'Lượt xem', 'value': tong_luot_xem}
    ]
    return render(request, 'myapp/dashboard.html', {
        'movies': movies,
        'users': users,
        'genres': genres,
        'actors': actors,
        'danh_gia': danh_gia,
        'tong_nguoi_dung': tong_nguoi_dung,
        'tong_phim': tong_phim,
        'tong_danh_gia': tong_danh_gia,
        'tong_luot_xem': tong_luot_xem,
        'top_phim_xem': top_phim_xem,
        'top_phim_danh_gia': top_phim_danh_gia,
        'top_user': top_user,
        'xem_theo_thang': xem_theo_thang,
        'danh_gia_theo_thang': danh_gia_theo_thang,
        'movie_query': movie_query,
        'review_query': review_query,  # ⚠️ Gửi ra template
        'stats': stats,
    })






@staff_member_required
def admin_movie_list(request):
    movies = Movie.objects.all()
    return render(request, 'myapp/movie_list.html', {'movies': movies})

@staff_member_required
def admin_add_movie(request):
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_movie_list')
    else:
        form = MovieForm()
    return render(request, 'myapp/movie_form.html', {'form': form})

@staff_member_required
def admin_edit_movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES, instance=movie)
        if form.is_valid():
            form.save()
            return redirect('admin_movie_list')
        else:
            print("❌ Form không hợp lệ:", form.errors)
    else:
        form = MovieForm(instance=movie)

    return render(request, 'myapp/movie_form.html', {'form': form})



@staff_member_required
def admin_delete_movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    movie.delete()
    return redirect('admin_movie_list')


from .models import TheLoai
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django import forms

# Form cho TheLoai
class TheLoaiForm(forms.ModelForm):
    class Meta:
        model = TheLoai
        fields = ['ten']
        labels = {'ten': 'Tên thể loại'}
        widgets = {
            'ten': forms.TextInput(attrs={'class': 'form-control'})
        }

# Danh sách thể loại
@staff_member_required
def admin_genre_list(request):
    genres = TheLoai.objects.all()
    return render(request, 'myapp/genre_list.html', {'genres': genres})

# Thêm thể loại
@staff_member_required
def admin_add_genre(request):
    if request.method == 'POST':
        form = TheLoaiForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_genre_list')
    else:
        form = TheLoaiForm()
    return render(request, 'myapp/genre_form.html', {'form': form})

# Sửa thể loại
@staff_member_required
def admin_edit_genre(request, genre_id):
    genre = get_object_or_404(TheLoai, id=genre_id)
    form = TheLoaiForm(request.POST or None, instance=genre)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('admin_genre_list')
    return render(request, 'myapp/genre_form.html', {'form': form})

# Xoá thể loại
@staff_member_required
def admin_delete_genre(request, genre_id):
    genre = get_object_or_404(TheLoai, id=genre_id)
    genre.delete()
    return redirect('admin_genre_list')






from .models import DienVien
from django.shortcuts import get_object_or_404

# Thêm diễn viên
def admin_add_actor(request):
    if request.method == "POST":
        ten = request.POST.get("ten", "").strip()
        if ten:
            DienVien.objects.create(ten=ten)
            messages.success(request, f"Đã thêm diễn viên '{ten}' thành công.")
        else:
            messages.error(request, "Tên diễn viên không được để trống.")
        return redirect("admin_dashboard")
    return render(request, "myapp/admin_add_actor.html")

# Sửa diễn viên
def admin_edit_actor(request, id):
    actor = get_object_or_404(DienVien, id=id)
    if request.method == "POST":
        ten_moi = request.POST.get("ten", "").strip()
        if ten_moi:
            actor.ten = ten_moi
            actor.save()
            messages.success(request, "Đã cập nhật diễn viên.")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Tên không được để trống.")
    return render(request, "myapp/admin_edit_actor.html", {"actor": actor})

# Xoá diễn viên
def admin_delete_actor(request, id):
    actor = get_object_or_404(DienVien, id=id)
    actor.delete()
    messages.success(request, f"Đã xoá diễn viên '{actor.ten}'.")
    return redirect("admin_dashboard")






@staff_member_required
def admin_delete_review(request, review_id):
    review = get_object_or_404(DanhGia, id=review_id)
    review.delete()
    return redirect('admin_dashboard')









