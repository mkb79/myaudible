from django.urls import path, re_path

from . import views


urlpatterns = [
    path('dashboard/', views.CreateLoginSessionView.as_view(), name='dashboard'),
    path('login/', views.CreateLoginSessionView.as_view(), name='audible_create_login'),
    path('login/<uuid:login_uuid>/<path:resource>', views.audible_login),
    path('login/<uuid:login_uuid>/', views.audible_login),
]
