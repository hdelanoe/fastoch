import os
from django.conf import settings
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from home.views import init_context
from inventory.models import Inventory

@login_required
def settings_view(request, *args, **kwargs):
    context = init_context()
    context['inventory_list'] = Inventory.objects.all()
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
