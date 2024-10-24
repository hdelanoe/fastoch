from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from .models import Backup, backup_columns
from dashboard.views import init_context

@login_required
def backup_view(request, *args, **kwargs):
    context = init_context()
    context['columns'] = backup_columns
    return render(request, "backup/backup.html", context) 

@login_required
def delete_backup(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            backup = Backup.objects.get(id=id)
            name = backup.name
            backup.delete()
            messages.success(request, f'Le backup {name} a bien été supprimé.')
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression du backup : {e}')   
        
    return redirect(reverse("backup"))   