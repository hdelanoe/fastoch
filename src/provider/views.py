import logging
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import ProtectedError
from django.core.paginator import Paginator

from home.views import init_context
from .models import Provider, provider_columns
from .forms import ProviderForm

logger = logging.getLogger('fastoch')

@login_required
def provider_view(request, query=None, *args, **kwargs):
    context = init_context()
    providers = context["provider_list"]
    
    if not query:
        query = request.GET.get('search', '')

    if query:
        providers = providers.filter(name__icontains=query)
        total = len(providers)
    else:
        total = providers.count()

    #paginator = Paginator(providers, 25)  # 25 produits par page
    #page_number = request.GET.get('page')
    #page_obj = paginator.get_page(page_number)  
    #pagin = int(len(page_obj.object_list)) + (page_obj.number-1)*25

    context["columns"] = provider_columns
    context["provider_list"] = providers
    #context["pages"] = page_obj
    context["total"] = total
    #context["len"] = pagin
    return render(request, "provider/provider.html", context) 

@login_required
def update_provider(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            provider = Provider.objects.get(id=id)
            print(provider)
            form = ProviderForm(request.POST)
            
            if form.is_valid():  # ✅ Toujours valider le formulaire avant d'accéder à `cleaned_data`
                provider.name = form.cleaned_data['name']
                provider.code = form.cleaned_data['code']
                provider.erase_multicode = form.cleaned_data['erase_multicode']  # ✅ Booléen correct
                provider.save()

                messages.success(request, f'Le provider {provider.name} a bien été modifié.')
                return HttpResponse("success")
            else:
                logger(form.errors)  # ✅ Debug si le form est invalide

        except Exception as e:
            logger(f"Erreur :{e}")
    raise Http404

@login_required
def delete_provider(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            provider = Provider.objects.get(id=id)
            name = provider.name
            provider.delete()
            messages.success(request, f'Le fournisseur {name} a bien été supprimé.')
        except ProtectedError:
            messages.error(request, f'Il existe encore des produits avec ce provider. Supprimez les d\'abord.')   
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression du provider : {e}')   
        
    return redirect(reverse("provider"))   
