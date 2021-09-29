from django import forms
from django.core.exceptions import ValidationError

from core.marketplaces import get_marketplaces_choices


MARKETPLACES = get_marketplaces_choices()


class AudibleCreateLoginForm(forms.Form):
    marketplace = forms.ChoiceField(choices=MARKETPLACES, initial='us')
    with_username = forms.BooleanField(required=False)

    def clean(self):
        cd = super().clean()
        marketplace = cd['marketplace']
        with_username = cd['with_username']

        if with_username and marketplace not in ('de', 'uk', 'us',):
            raise ValidationError('username login is not allowed for this marketplace.')


class AuthFileImportForm(forms.Form):
    auth_file = forms.FileField()
    password = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput,
        required=False
    )

