from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.contrib.auth.models import User


class UserSettingsView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'registration/profile_settings.html'
    fields = ['username', 'email']
    success_url = reverse_lazy('user:settings')

    def get_object(self):
        return self.request.user
