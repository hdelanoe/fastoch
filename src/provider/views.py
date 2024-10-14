from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from dashboard.views import init_context
from .models import Provider, provider_columns
from .forms import ProviderForm

@login_required
def provider_view(request, *args, **kwargs):
    context = init_context()
    context["columns"] = provider_columns
    return render(request, "provider/provider.html", context) 

@login_required
def update_provider(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        provider = Provider.objects.get(id=id)
        form = ProviderForm(request.POST)
        provider.name = form.data['name']
        #provider.n_tva = form.data['n_tva']
        #provider.tva = form.data['tva']
        provider.save()
        
    return redirect(reverse("provider"))  
