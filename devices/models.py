from datetime import datetime, timezone

from core.utils import get_data_from_uploaded_auth_file

from django.conf import settings
from django.db import models, transaction
from django.core.validators import RegexValidator, MaxLengthValidator


class AudibleDevice(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='audible_devices',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    country_code = models.CharField(max_length=5)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if hasattr(self, 'device_info'):
            return self.device_info.device_name
        return 'unknown Audible device'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('own_device_detail', kwargs={'pk' : self.pk})

    @classmethod
    def create_from_registration(cls, data, user):
        expires = data['expires']
        if isinstance(expires, (int, float)):
            expires = datetime.fromtimestamp(expires, timezone.utc)

        device = cls(
            user=user, country_code=data.get('locale_code')
        )
        bearer = BearerToken(
            device=device,
            access_token=data.get('access_token'),
            refresh_token=data.get('refresh_token'),
            access_token_expires=expires
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

        return cls

    @classmethod
    def create_from_file_import(cls, file, password, user):
        data = get_data_from_uploaded_auth_file(file, password)

        return cls.create_from_registration(data=data, user=user)
        

class BearerToken(models.Model):
    device = models.OneToOneField(
        AudibleDevice,
        related_name='bearer',
        on_delete=models.CASCADE,
        primary_key=True
    )
    access_token = models.TextField(
        max_length=500,
        validators=[
            RegexValidator(regex=r'^Atna\|.*$'),
            MaxLengthValidator(500)
        ]
    )
    access_token_expires = models.DateTimeField()
    refresh_token = models.TextField(
        max_length=500,
        validators=[
            RegexValidator(regex=r'^Atnr\|.*$'),
            MaxLengthValidator(500)
        ]
    )


class CustomerInfo(models.Model):
    device = models.OneToOneField(
        AudibleDevice,
        related_name='customer_info',
        on_delete=models.CASCADE,
        primary_key=True
    )
    account_pool = models.CharField(max_length=20)
    user_id = models.CharField(max_length=100)
    home_region = models.CharField(max_length=10)
    name = models.CharField(max_length=50)
    given_name = models.CharField(max_length=20)


class DeviceInfo(models.Model):
    device = models.OneToOneField(
        AudibleDevice,
        related_name='device_info',
        on_delete=models.CASCADE,
        primary_key=True
    )
    device_name = models.CharField(max_length=100)
    device_serial_number = models.CharField(max_length=50)
    device_type = models.CharField(max_length=20)


class MessageAuthenticationCode(models.Model):
    device = models.OneToOneField(
        AudibleDevice,
        related_name='mac_dms',
        on_delete=models.CASCADE,
        primary_key=True)
    adp_token = models.TextField(
        max_length=1800,
        validators=[
            RegexValidator(
                regex=r'^{enc:.*}{key:.*}{iv:.*}{name:.*}{serial:Mg==}$'
            ),
            MaxLengthValidator(1800)
        ]
    )
    device_cert = models.TextField(max_length=2000)


class StoreAuthenticationCookie(models.Model):
    device = models.OneToOneField(
        AudibleDevice,
        related_name='store_cookie',
        on_delete=models.CASCADE,
        primary_key=True
    )
    cookie = models.TextField(
        max_length=300,
        validators=[
            MaxLengthValidator(300)
        ]
    )


class WebsiteCookie(models.Model):
    device = models.ForeignKey(
        AudibleDevice,
        on_delete=models.CASCADE,
        related_name='website_cookies'
    )
    country_code = models.CharField(max_length=5)
    name = models.CharField(max_length=30)
    value = models.TextField()

