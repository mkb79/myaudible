from django.http import Http404, HttpResponse
from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import (AudibleCreateLoginForm)
from core.login import session_pool


@csrf_exempt
def register_device(request, login_uuid, resource=None, *args, **kwargs):
    s_obj = session_pool.get_session_by_uuid(login_uuid)
    if not s_obj:
        raise Http404('Login session does not exist.')

    if resource:
        if request.META['QUERY_STRING']:
            resource += '?' + request.META['QUERY_STRING']

        data = None
        if request.method == 'POST':
            data = request.POST
        s_obj.session.request(method=request.method, url=resource, data=data)

    # we are finished
    # TODO: write success page
    if s_obj.is_logged_in:
        s_obj.close_session()
        print(s_obj.session._access_token)
        return

    status = s_obj.session._last_response.status_code
    content_type = s_obj.session._last_response.headers['Content-Type']
    content = s_obj.session._last_response_content

    return HttpResponse(
        content,
        status=status,
        content_type=content_type
    )


class RegisterDeviceView(LoginRequiredMixin, FormView):

    form_class = AudibleCreateLoginForm
    template_name = 'devices/create-login.html'

    def get(self, request, *args, **kwargs):
        # remove old login session if exists
        session_key = self.request.session.session_key
        if session_pool.has_session(session_key):
            session_pool.remove_session(session_key)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        cd = form.cleaned_data
        session_key = self.request.session.session_key

        s_obj = session_pool.create_session(
            session_key=session_key,
            country_code=cd['marketplace'],
            with_username=cd['with_username']
        )

        proxy_url = self.request.build_absolute_uri(
            reverse(register_device, kwargs={'login_uuid': s_obj.session_uuid})
        )
        s_obj.start_session(proxy_url=proxy_url)
        
        return redirect(register_device, login_uuid=s_obj.session_uuid)

