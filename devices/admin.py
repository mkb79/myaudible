import json
from datetime import datetime

from django.contrib import admin
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path
from audible.aescipher import AESCipher

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


def detect_auth_data_encryption(data):
    try:
        data = json.loads(data)
        if "adp_token" in data:
            return False
        elif "ciphertext" in data:
            return "json"
    except UnicodeDecodeError:
        return "bytes"


def process_import(file, password, user):
    data = file.read()
    encryption = detect_auth_data_encryption(data)
    if encryption:
        crypter = AESCipher(password=password)
        if encryption == "json":
            encrypted_dict = json.loads(data)
            data = crypter.from_dict(encrypted_dict)
        elif encryption == "bytes":
            data = crypter.from_bytes(data)
    data = json.loads(data)
    device = AudibleDevice(
        user=user, country_code=data.get('locale_code')
    )
    bearer = BearerToken(
        device=device,
        access_token=data.get('access_token'),
        refresh_token=data.get('refresh_token'),
        access_token_expires=datetime.fromtimestamp(data['expires'])
    )
    customer_info = CustomerInfo(
        device=device, **data.get('customer_info')
    )
    device_info = DeviceInfo(
        device=device, **data.get('device_info')
    )
    mac_dms = MessageAuthenticationCode(
        device=device,
        adp_token=data.get('adp_token'),
        device_cert=data.get('device_private_key')
    )
    store_cookie = StoreAuthenticationCookie(
        device=device,
        cookie=data.get('store_authentication_cookie',{}).get('cookie')
    )

    with transaction.atomic():
        device.save()
        bearer.save()
        customer_info.save()
        device_info.save()
        mac_dms.save()
        store_cookie.save()

    for name, value in data.get('website_cookies', {}).items():
        device.website_cookies.create(
            country_code=data.get('locale_code'),
            name=name,
            value=value
        )


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
    list_filter = ('last_modified', 'created')
    list_display = ('user', 'device_name', 'created', 'last_modified')
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
                process_import(
                    file=request.FILES.get('auth_file'),
                    password=request.POST.get('password'),
                    user=request.user)
                self.message_user(request, 'Your auth file has been imported')
                return redirect('..')
        else:
            form = AuthFileImportForm()
        return render(
            request, 'devices/auth-file-import-form.html', {'form': form}
        )

