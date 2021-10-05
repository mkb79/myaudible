from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import path

from .models import (
    AudibleDevice,
    BearerToken,
    CustomerInfo,
    DeviceInfo,
    MessageAuthenticationCode,
    StoreAuthenticationCookie,
    WebsiteCookie)
from .forms import AuthFileImportForm


class BearerTokenInline(admin.StackedInline):
    model = BearerToken
    classes = ['collapse']


class CustomerInfoInline(admin.StackedInline):
    model = CustomerInfo
    classes = ['collapse']


class DeviceInfoInline(admin.StackedInline):
    model = DeviceInfo


class MessageAuthenticationCodeInline(admin.StackedInline):
    model = MessageAuthenticationCode
    classes = ['collapse']


class StoreAuthenticationCookieInline(admin.StackedInline):
    model = StoreAuthenticationCookie
    classes = ['collapse']


class WebsiteCookieInline(admin.StackedInline):
    model = WebsiteCookie
    classes = ['collapse']


@admin.register(AudibleDevice)
class AudibleDeviceAdmin(admin.ModelAdmin):
    inlines = [
        DeviceInfoInline,
        CustomerInfoInline,
        MessageAuthenticationCodeInline,
        BearerTokenInline,
        StoreAuthenticationCookieInline,
        WebsiteCookieInline
    ]
    list_filter = ('last_modified', 'created_at')
    list_display = ('user', 'device_name', 'created_at', 'last_modified')
    change_list_template = 'audible_devices_changelist.html'

    def device_name(self, obj):
        return obj.device_info.device_name

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(id=request.user.id)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path('import-auth-file/', self.import_auth_file)
        ]
        return new_urls + urls

    def import_auth_file(self, request):
        if request.method == 'POST':
            form = AuthFileImportForm(request.POST, request.FILES)
            if form.is_valid():
                AudibleDevice.create_from_file_import(
                    file=request.FILES.get('auth_file'),
                    password=request.POST.get('password'),
                    user=request.user
                )
                self.message_user(request, 'Your auth file has been imported')
                return redirect('..')
        else:
            form = AuthFileImportForm()
        return render(
            request, 'devices/auth-file-import-form.html', {'form': form}
        )

