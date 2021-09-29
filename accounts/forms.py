from django.contrib.auth.forms import UserCreationForm


class MyAudibleUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)
