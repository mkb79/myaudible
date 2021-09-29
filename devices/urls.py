from django.urls import path

from . import views


urlpatterns = [
    path('dashboard/', views.RegisterDeviceView.as_view(), name='dashboard'),
    path('register-device/', views.RegisterDeviceView.as_view(), name='audible_add_device'),
    path('register-device/<uuid:login_uuid>/<path:resource>', views.register_device),
    path('register-device/<uuid:login_uuid>/', views.register_device),
]

