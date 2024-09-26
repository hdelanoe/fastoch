import os
from django.conf import settings
from django.http import Http404, HttpResponse
from django.urls import reverse
import pandas as pd
from pdf2image import convert_from_path

from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages

from helpers.mistral import Mistral_API, format_content_from_image_path
from .forms import FileForm, QuestionForm, ProductForm
from inventory.models import Inventory, Product, StockTransaction, Kesia2_column_names


@login_required
def inventory_view(request, id=None, response=0, *args, **kwargs):
    inventory_obj = Inventory.objects.get(id=id)
    inventory_list = Inventory.objects.all()
    context = {
        "inventory": inventory_obj,
        "inventory_list": inventory_list,
        "columns": Kesia2_column_names.values(),
        "response": response,
        "products": inventory_obj.products.all(),

        
    }
    return render(request, "inventory/inventory.html", context) 

@login_required
def upload_pdf(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES['document']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            pdf_path = fs.path(filename)
            pages = convert_from_path(pdf_path, 100)
            inventory = Inventory.objects.get(id=id)
            api = Mistral_API()
            image_content = []
            try:
                for count, page in enumerate(pages):
                    page.save(f'{settings.MEDIA_ROOT}/pdf{count}.jpg', 'JPEG')
                    jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                    image_content.append(format_content_from_image_path(jpg_path))
                try:
                    json_data = api.extract_json_from_image(image_content)
                    for jd in json_data:
                        ean = str(jd.get('ean')).replace(' ', '')
                        if not ean.isdigit():
                            ean = None
                        product = Product.objects.create(
                            fournisseur=jd.get('fournisseur'),
                            ean=ean,
                            description=jd.get('description'),
                            quantity=jd.get('quantity'),
                            achat_brut=jd.get('achat_brut'),
                            achat_tva=jd.get('achat_tva'),
                            achat_net=jd.get('achat_net'),
                        )
                        product.save()
                        transaction = StockTransaction.objects.create(
                            product=product,
                            quantity=product.quantity
                        )
                        transaction.save()
                        inventory.products.add(product)
                        inventory.transaction_list.add(transaction)
                    inventory.save()
                    messages.success(request, "Your inventory has been updated.")
                except Exception as e:
                    messages.error(request, f'error while extracting {e}')
                for count, page in enumerate(pages):
                    jpg_path = fs.path(f'{settings.MEDIA_ROOT}/pdf{count}.jpg')
                    fs.delete(jpg_path)

            except Exception as e:
                messages.error(request, f'error while parsing {e}')
            fs.delete(pdf_path)
        except Exception as e:
            messages.error(request, f'error while saving {e}')
    return redirect(reverse("inventory", args=[id, 0]))

@login_required
def export_file(request, id=None, data_types=None, *args, **kwargs):
    inventory_obj = Inventory.objects.get(id=id)
    columns = Kesia2_column_names.values()
    df = pd.DataFrame([p.to_dict() for p in inventory_obj.products.all()], columns = columns)
    file_path = f'{settings.MEDIA_ROOT}/{inventory_obj.name}.xlsx'
    df.to_excel(file_path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
def update_product(request, inventory=None, product=None, *args, **kwargs):
    if request.method == 'POST':
        product_obj = Product.objects.get(id=product)
        form = ProductForm(request.POST)
        product_obj.description = form.data['description']
        product_obj.save()
    return redirect(reverse("inventory", args=[id, 1]))    

@login_required
def ask_question(request, id=None, *args, **kwargs):
    inventory_obj = Inventory.objects.get(id=id)
    if request.method == 'POST':
        api = Mistral_API()
        form = QuestionForm(request.POST)
        inventory_obj.last_response = api.chat(form.data['question'], inventory_obj.products.all())
        inventory_obj.save()
    print(inventory_obj.last_response)    
    return redirect(reverse("inventory", args=[id, 1]))