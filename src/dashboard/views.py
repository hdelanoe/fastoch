import logging
import os
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse
from django.core.files.storage import FileSystemStorage

from inventory.forms import ImportForm
from inventory.models import Inventory, Product, iProduct
from delivery.models import Delivery
from helpers.pyzbar import bar_decoder
from helpers.preprocesser import convert_heic_to_png
from home.views import init_context

logger = logging.getLogger('fastoch')

@login_required
def dashboard_view(request):
    context = init_context()
    request.session['context'] = 'dashboard'
    if not context["inventory_list"] :
        Inventory.objects.create(
            name="Inventaire", is_current=True, is_waiting=False)
        Inventory.objects.create(
            name="Reception", is_current=False, is_waiting=True)
        return redirect(reverse("dashboard"))
    return render(request, "dashboard/dashboard.html", context)

@login_required
def create_inventory(request):
    if request.method=='POST':
        try:
            inventories=Inventory.objects.all()
            if not inventories:
                Inventory.objects.create(
                    name=request.POST.get('name', "My inventory"),
                    is_current=True, is_waiting=False)
            else:
                Inventory.objects.create(name=request.POST.get('name', "My inventory"))
            messages.success(request, "Your inventory has been created.")
        except Inventory.DoesNotExist:
            messages.error(request, "Error while create your inventory.")
    return redirect(reverse("dashboard"))

@login_required
def add_product_from_photo(request):
    if request.method == 'POST':
        try:
            form = ImportForm(request.POST)
            uploaded_file = request.FILES['document']
            number = form.data['number']
            container = bool(form.data['container'])
            logger.debug(f'container : {container}')
            filename, file_extension = os.path.splitext(uploaded_file.name)
            fs = FileSystemStorage()
            file = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.path(file)
            logger.debug(f'file_path: {file_path}, type: {type(file_path)}')
            if file_extension == ".png" or file_extension== ".jpeg" or file_extension== ".jpg" or file_extension == ".heic":
                if file_extension == ".heic":
                    try:
                        png_path = convert_heic_to_png(filename, file_path)
                        logger.debug(f"Filepath for decoding: {png_path}")
                        logger.debug(f"File exists: {os.path.exists(png_path)}")
                        if not png_path:
                            messages.error(request, f"Erreur lors de la conversion du fichier HEIC.")
                            return redirect(reverse("dashboard"))

                        # Décoder le fichier PNG
                        barcode = bar_decoder.decode(png_path)
                    except Exception as e:
                        logger.error(f"Error processing HEIC file: {e}")
                        messages.error(request, f"Erreur lors du traitement du fichier HEIC.")
                        barcode = None
                    finally:
                        # Supprimer le fichier PNG temporaire s'il a été créé
                        if png_path and os.path.exists(png_path):
                            os.remove(png_path)
                elif file_extension == ".png" or file_extension== ".jpeg" or file_extension== ".jpg":
                    barcode = bar_decoder.decode(file_path)
                if barcode is None:
                    messages.warning(request, f'Aucun code-barres détecté.')
                    fs.delete(file_path)
                    return redirect(reverse("dashboard"))
                # Create product from barcode
                product, created = Product.objects.get_or_create(ean=barcode)
                if created:
                        product.multicode=product.ean
                        product.save()
                        logger.debug("product created!")
                iproduct, created = iProduct.objects.get_or_create(product=product)
                iproduct.quantity = number
                if container is True:
                    iproduct.container_name = Inventory.objects.get(is_current=True).name
                    iproduct.save()
                    fs.delete(file_path)
                    messages.success(request, f'produit {product.ean} mis à jour dans l\'inventaire !')
                    return redirect(f'{reverse("inventory", args=[0])}?search={product.ean}')
                else:
                    delivery = Delivery.objects.create()
                    iproduct.container_name = delivery.date_time
                    iproduct.save()
                    fs.delete(file_path)
                    messages.success(request, f'produit {product.ean} mis à jour dans la livraison !')
                    return redirect(reverse("delivery", args=[delivery.id]))
            else:
                messages.error(request, f'extension {file_extension} non supportée.')
                if fs and file_path:
                    fs.delete(file_path)
                return redirect(reverse("dashboard"))
        except Exception as e:
            logger.error(f'{e}')
            messages.error(request, f'Erreur lors de la sauvegarde du fichier.')
        
    return redirect(reverse("dashboard"))


