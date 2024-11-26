from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import ProtectedError
from django.core.paginator import Paginator

from home.views import init_context
from .models import Provider, provider_columns
from .forms import ProviderForm

@login_required
def provider_view(request, *args, **kwargs):
    context = init_context()

    query = request.GET.get('search', '')  # Récupère le texte de recherche
    providers = context["provider_list"]
    # Filtre les produits si une recherche est spécifiée
    if query:
        providers = providers.filter(name__icontains=query)
        total = len(providers)
    else:
        total = providers.count()

    paginator = Paginator(providers, 25)  # 25 produits par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)  
    pagin = int(len(page_obj.object_list)) + (page_obj.number-1)*25

    context["columns"] = provider_columns
    context["provider_list"] = page_obj.object_list
    context["pages"] = page_obj
    context["total"] = total
    context["len"] = pagin
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

@login_required
def delete_provider(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            provider = Provider.objects.get(id=id)
            name = provider.name
            provider.delete()
            messages.success(request, f'Le provider {name} a bien été supprimé.')
        except ProtectedError:
            messages.error(request, f'Il existe encore des produits avec ce provider. Supprimez les d\'abord.')   
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression du provider : {e}')   
        
    return redirect(reverse("provider"))   
