from django.db import models
from django.core.validators import RegexValidator, MaxLengthValidator


class AudibleDevice(models.Model):
    user = models.ForeignKey(
        'auth.User',
        related_name='audible_devices',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    country_code = models.CharField(max_length=5)

    def __str__(self):
        if hasattr(self, 'device_info'):
            return self.device_info.device_name
        return 'unknown Audible device'


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

