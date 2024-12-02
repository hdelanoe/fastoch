import os
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse
from django.core.files.storage import FileSystemStorage

from inventory.forms import ImportForm
from inventory.models import Inventory, Product
from helpers.pyzbar import bar_decoder
from heic2png import HEIC2PNG
from home.views import init_context

@login_required
def dashboard_view(request):
    context = init_context()
    if not context["current_inventory"] :
        return render(request, "dashboard/dashboard_new_inventory.html", context)
    inventory = Inventory.objects.get(is_current=True)
    context["inventory"] = inventory
    return render(request, "dashboard/dashboard.html", context) 

@login_required
def create_inventory(request):
    if request.method=='POST':
        try:
            inventories=Inventory.objects.all()
            if not inventories:
                Inventory.objects.create(
                    name=request.POST.get('name', "My inventory"),
                    is_current=True)
            else:    
                Inventory.objects.create(name=request.POST.get('name', "My inventory"))
            messages.success(request, "Your inventory has been created.")
        except Inventory.DoesNotExist:
            messages.error(request, "Error while create your inventory.")
    return redirect(reverse("dashboard"))

@login_required
def add_product_from_photo(request):
    if request.method == 'POST':
            form = ImportForm(request.POST)
            uploaded_file = request.FILES['document']
            number = form.data['number']
            filename, file_extension = os.path.splitext(uploaded_file.name)
            if file_extension == ".png":
                    fs = FileSystemStorage()
                    file = fs.save(uploaded_file.name, uploaded_file)
                    file_path = fs.path(file)
                    barcode = bar_decoder.decode(file_path)
                    if barcode is None:
                         messages.warning(request, f'Aucun code-barres détecté.')
                         return redirect(reverse("dashboard"))
                    product, created = Product.objects.get_or_create(ean=barcode)
                    if created:
                         product.multicode=product.ean
                    product.quantity = number

                    product.save()
                    inventory = Inventory.objects.get(is_current=True)
                    inventory.products.add(product)
                    inventory.save()
                    messages.success(request, f'produit {product.ean} mis à jour dans l\'inventaire !')
                    fs.delete(file_path)
            else:
               messages.error(request, f'extension {file_extension} non supportée.')
               return redirect(reverse("dashboard"))     
            '''
             elseif file_extension == ".heic":
                img = HEIC2PNG(uploaded_file, quality=90)
                img.save()
                barcode = bar_decoder.decode(img)
            '''
    return redirect(reverse("dashboard"))
