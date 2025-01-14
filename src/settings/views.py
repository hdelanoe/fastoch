import os
from django.conf import settings
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import redirect, render
from home.views import init_context
from inventory.models import Inventory
from .models import Settings
from .forms import SettingsForm

@login_required
def settings_view(request, *args, **kwargs):
    context = init_context()
    settings, created = Settings.objects.get_or_create(id=1)
    if created:
        settings.erase_multicode=False
    context['inventory_list'] = Inventory.objects.all()
    context['erase_multicode'] = settings.erase_multicode
    return render(request, "settings/settings.html", context)

@login_required
def documentation_view(request, *args, **kwargs):
    context = init_context()
    return render(request, "settings/documentation.html", context)

@login_required
def download_logfile(request):
    if os.path.exists(settings.LOGFILE_PATH):
        with open(settings.LOGFILE_PATH, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(settings.LOGFILE_PATH)
            return response
    raise Http404

@login_required
def update_preferences(request, *args, **kwargs):
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        settings, created = Settings.objects.get_or_create(id=1)
        erase = bool(form.data['erase'])
        settings.erase_multicode = erase
        settings.save()
        messages.success(request, "Preferences mis a jour.")
    return redirect(reverse("settings"))
