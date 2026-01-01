from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Movie, DanhGia

class LoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
class AvatarForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['avatar']

# from allauth.account.forms import SignupForm
# from django import forms

# class CustomSignupForm(SignupForm):
#     def save(self, request):
#         user = super().save(request)
#         # Bạn có thể lưu thông tin bổ sung ở đây
#         return user
from django import forms
from .models import Movie

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = '__all__' 
        widgets = {
            'maphim': forms.TextInput(attrs={'class': 'form-control'}),
            'ten_phim': forms.TextInput(attrs={'class': 'form-control'}),
            'trailer_url': forms.URLInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'the_loai': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'mo_ta': forms.Textarea(attrs={'class': 'form-control'}),
            'dao_dien': forms.TextInput(attrs={'class': 'form-control'}),
            'dien_vien': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'ngay_phat_hanh': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'thoi_luong': forms.NumberInput(attrs={'class': 'form-control'}),
            'anh_bia': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'trang_thai': forms.Select(attrs={'class': 'form-control'}),
        }
class DanhGiaForm(forms.ModelForm):
    class Meta:
        model = DanhGia
        fields = '__all__' 

# forms.py
from django import forms
from .models import Movie

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = '__all__'
        widgets = {
            'the_loai': forms.CheckboxSelectMultiple(),
            'dien_vien': forms.CheckboxSelectMultiple(), 
        }

        
