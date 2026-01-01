from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.urls import path, include
from .views import search_movies, lich_su_xem, xem_phim, the_loai,movie_review
from myapp.views import login_view
from django.views.generic import TemplateView
from .views import update_fullname
from django.contrib.auth import views as auth_views
from django.urls import path
from django.contrib import admin

urlpatterns = [
    
    path('', views.home, name='home'),
    path("gioithieu/", views.gioithieu, name="gioithieu"),

        # Giới thiệu và điều khoản
    path('gioithieu/', views.gioithieu, name='gioithieu'),
    path("dieukhoan/", views.dieukhoan, name="dieukhoan"),
    path("quyen/", views.quyen, name="quyen"),
    path('update-avatar/', views.update_avatar, name='update_avatar'),
    path('log/login/', login_view, name='login'),
    path('log/profile/', views.profile, name='profile'),
    path('toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('phim/<int:maphim>/', views.chitietphim, name='chitietphim'),

    path("search/", search_movies, name="search_movies"),
    path('lich-su-xem/', views.lich_su_xem, name='lich_su_xem'),
    path("update-fullname/", update_fullname, name="update_fullname"),
    path('the-loai/<str:ten>/', the_loai, name='the_loai'),
    path('chitietphim/<str:maphim>/', views.chitietphim, name='chitietphim'),
    path("phim/<int:movie_id>/review/", movie_review, name="movie_review"),
    path('recommend/', views.recommend_movies, name='recommend'),
    path('goi-y/', views.recommended_movies_view, name='recommended_movies'),   
    path('reviews/delete/', views.delete_review, name='delete_review'),
    path('api/edit-review/', views.edit_review, name='edit_review'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('movies/', views.admin_movie_list, name='admin_movie_list'),
    path('movies/add/', views.admin_add_movie, name='admin_add_movie'),
    path('movies/edit/<int:movie_id>/', views.admin_edit_movie, name='admin_edit_movie'),
    path('movies/delete/<int:movie_id>/', views.admin_delete_movie, name='admin_delete_movie'),
    # path('users/', views.admin_user_list, name='admin_user_list'),
    path('genres/', views.admin_genre_list, name='admin_genre_list'),
    path('genres/add/', views.admin_add_genre, name='admin_add_genre'),
    path('genres/<int:genre_id>/edit/', views.admin_edit_genre, name='admin_edit_genre'),
    path('genres/<int:genre_id>/delete/', views.admin_delete_genre, name='admin_delete_genre'),
    # path('admin/thong-ke/', views.admin_thong_ke, name='admin_thong_ke'),
    path("actor/add/", views.admin_add_actor, name="admin_add_actor"),
    path("actor/<int:id>/edit/", views.admin_edit_actor, name="admin_edit_actor"),
    path("actor/<int:id>/delete/", views.admin_delete_actor, name="admin_delete_actor"),
    path('review/delete/<int:review_id>/', views.admin_delete_review, name='admin_delete_review'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
