from django.urls import include, path

from . import views


urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('register/', views.RegisterFormView.as_view(), name='account_register'),
    path('profile/', views.AccountProfileView.as_view(), name='account_profile'),
    path('edit/', views.AccountUpdateView.as_view(), name='account_edit'),
]
