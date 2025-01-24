import os
import logging
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
from datetime import date



logger = logging.getLogger('fastoch')

@login_required
def settings_view(request, *args, **kwargs):
    context = init_context()
    settings, created = Settings.objects.get_or_create(id=1)
    context['inventory_list'] = Inventory.objects.all()
    context['erase_multicode'] = settings.erase_multicode
    return render(request, "settings/settings.html", context)

@login_required
def documentation_view(request, *args, **kwargs):
    context = init_context()
    return render(request, "settings/documentation.html", context)

@login_required
def download_logfile(request):
    logfile = str(settings.LOG_FILE_PATH)
    if os.path.exists(logfile):
        logger.debug(f'log path -> {logfile}')
        with open(logfile, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="text/plain")
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(logfile)
            return response
    raise Http404

@login_required
def update_preferences(request, *args, **kwargs):
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        settings, created = Settings.objects.get_or_create(id=1)
        # Récupération de la valeur du champ erase_multicode
        erase_multicode_value = form.data['erase_multicode']
        erase_multicode = erase_multicode_value == "Oui"  # Convertit explicitement en booléen
        settings.erase_multicode = erase_multicode

        pagin_value = int(form.data['pagin'])
        settings.pagin = pagin_value
        settings.save()
        logger.debug(f'new settings : erase_multicode -> {settings.erase_multicode}')
        logger.debug(f'new settings : pagin -> {settings.pagin}')
        messages.success(request, "Preferences mis a jour.")
    return redirect(reverse("settings"))

@login_required
def delete_media_files(request, *args, **kwargs):
    directory_path = settings.MEDIA_DIRECTORY_PATH
    logger.debug(f'media path -> {directory_path}')
    try:
        files = os.listdir(directory_path)
        logger.debug(f'files -> {files}')
        for file in files:
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        messages.success(request, "Medias supprimes.")
    except OSError as e:
        messages.error(request, f'Erreur lors de la suppresion des medias : {e}')
    return redirect(reverse("settings"))
