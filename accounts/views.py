from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, UpdateView
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin

from .forms import MyAudibleUserCreationForm


class RegisterFormView(SuccessMessageMixin, FormView):
    form_class = MyAudibleUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('account_profile')
    success_message = "Account was created successfully."

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class AccountProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'


class AccountUpdateView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    template_name = 'accounts/edit.html'
    fields = ['username', 'email']
    model = get_user_model()
    success_message = "Account was edited successfully."
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_object(self, queryset=None):
        obj = self.model.objects.get(username=self.request.user)
        return obj
