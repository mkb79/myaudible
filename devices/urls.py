from django.urls import path

from . import views


urlpatterns = [
    path('dashboard/', views.RegisterDeviceView.as_view(), name='dashboard'),
    path('add-device/', views.RegisterDeviceView.as_view(), name='audible_add_device'),
    path('add-device/<uuid:login_uuid>/<path:resource>', views.register_device),
    path('add-device/<uuid:login_uuid>/', views.register_device),
    path('import-file/', views.ImportAuthFileView.as_view(), name='import_auth_file'),
    path('<int:pk>/', views.OwnDevicesDetailView.as_view(), name='own_device_detail'),
    path('', views.OwnDevicesListView.as_view(), name='own_devices_list')
]

