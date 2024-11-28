from django.shortcuts import render

from django.contrib.auth.decorators import login_required

from home.views import init_context

@login_required
def settings_view(request, *args, **kwargs):
    context = init_context()
    return render(request, "settings/settings.html", context)
