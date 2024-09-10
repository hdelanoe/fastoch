from django.urls import reverse
import pandas
import camelot
import numpy
import re
from numpy.dtypes import StringDType
from django.core.files.storage import FileSystemStorage

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages

from customers.models import Customer
from inventory.models import Inventory, Product, StockEntry


Pronatura_dictionary = {
    "quantity": "Nb Colis / Pièce",
    "lot_id": "N° lot",
    "description": "Désignation",
    "weight": "Poids net / brut",
    "price": "Prix",
    "discount": "% remise",
    "net_price": "Prix Net",
    "unit": "U",
    "tva": "% TVA",
    "net": "Montant net H.T.",
}

@login_required
def inventory_view(request, id=None, data_types=None, *args, **kwargs):
    inventory_obj = get_inventory_with_email(request.user.email)
    context = {
        "products": inventory_obj.products.all(),
        "inventory_list": [inventory_obj],
        "inventory_name": inventory_obj.name,
        "id": inventory_obj.id,
        "data_types":inventory_obj.get_dtypes_as_list(),
    }
    return render(request, "inventory/inventory.html", context) 

@login_required
def upload_file(request, id=None, *args, **kwargs):
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES['document']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            try:
                file_path = fs.path(filename)
                tables = camelot.read_pdf(file_path, pages='all')
                df_list = []
                for table in tables: 
                    df_list.append(table.df)
                
                # concatenate df
                df = pandas.concat(df_list)
                df.dropna(axis=1, inplace=True)
                # get columns
                parse_columns = numpy.strings.replace(numpy.array(df.iloc[0], dtype=StringDType()), '\n', '')
                data_df = pandas.DataFrame(data=None, columns = parse_columns)
                df = df.drop([0])
                for x in range(len(df.index)):
                    data_df.loc[x] = df.values[x]

                # for other artifacts
                #data_df.replace('', numpy.nan, inplace=True)
                #data_df.dropna(axis=0, inplace=True)
                pcstr = ''
                for v in parse_columns:
                    pcstr += f',{v}'
                try:
                    inventory_obj = Inventory.objects.get(id=id)
                    inventory_obj.dtypes_array = pcstr[1:]
                    tmp_product_list = []
                    tmp_entry_list = []
                    for values in data_df.iloc:
                        product = Product.objects.create(
                            lot_id=values[Pronatura_dictionary.get('lot_id')],
                            description=values[Pronatura_dictionary.get('description')],
                            unit=values[Pronatura_dictionary.get('unit')],
                            name = values[Pronatura_dictionary.get('description')][:20]
                        )
                        try: product.quantity = int(values[Pronatura_dictionary.get('quantity')])
                        except: None
                        try: product.weight = float(re.split('\n', values[Pronatura_dictionary.get('weight')].replace(',', '.'))[0])
                        except: None  
                        try: product.price = float(values[Pronatura_dictionary.get('price')].replace(',', '.'))
                        except: None
                        try: product.discount = float(values[Pronatura_dictionary.get('discount')].replace(',', '.'))
                        except: None  
                        try: product.net_price = float(values[Pronatura_dictionary.get('net_price')].replace(',', '.'))
                        except: None
                        try: product.tva = float(values[Pronatura_dictionary.get('tva')].replace(',', '.'))
                        except: None
                        try: product.net = float(values[Pronatura_dictionary.get('net')].replace(',', '.'))
                        except: None

                        tmp_product_list.append(product)
                        entry = StockEntry.objects.create(
                            product=product,
                            quantity=product.quantity
                        )
                        tmp_entry_list.append(entry)
                    for e in tmp_entry_list:
                        inventory_obj.entry_list.add(e)
                    for p in tmp_product_list:
                        inventory_obj.products.add(p)  
                    inventory_obj.save()

                    messages.success(request, "Your inventory has been updated.")
                except Exception as e:
                    messages.error(request, f"Error while create your inventory. {e}")
            except Exception as e:
                messages.error(request, f"Error while update your inventory. {e}")
            fs.delete(file_path)
        except Exception as e:
            messages.error(request, f"Error while upload file. {e}")    
    return redirect(reverse("inventory", args=[id]))

def get_inventory_with_email(email):
    customer = Customer.get_customer_by_user_email(email)
    return Inventory.objects.get(customer=customer)