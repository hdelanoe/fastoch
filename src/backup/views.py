from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Backup, backup_columns
from dashboard.views import init_context

@login_required
def backup_view(request, *args, **kwargs):
    context = init_context()
    context['columns'] = backup_columns
    return render(request, "backup/backup.html", context) 
