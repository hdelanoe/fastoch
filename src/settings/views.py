from django.shortcuts import render

from django.contrib.auth.decorators import login_required

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
