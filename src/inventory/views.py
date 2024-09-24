import os
from django.conf import settings
from django.http import Http404, HttpResponse
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
from inventory.models import Inventory, Product, StockTransaction, Kesia2_column_names


@login_required
def inventory_view(request, id=None, *args, **kwargs):
    inventory_obj = Inventory.objects.get(id=id)
    inventory_list = Inventory.objects.all()
    context = {#
        "inventory": inventory_obj,
        "inventory_list": inventory_list,
        "columns": Kesia2_column_names.values(),
        
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
                    for values in data_df.iloc:
                        product = Product.objects.create(
                            lot_id=values[Kesia2_column_names.get('lot_id')],
                            description=values[Kesia2_column_names.get('description')],
                            unit=values[Kesia2_column_names.get('unit')],
                            name = values[Kesia2_column_names.get('description')][:20]
                        )
                        try: product.quantity = int(values[Kesia2_column_names.get('quantity')])
                        except: None
                        try: product.weight = float(re.split('\n', values[Kesia2_column_names.get('weight')].replace(',', '.'))[0])
                        except: None  
                        try: product.price = float(values[Kesia2_column_names.get('price')].replace(',', '.'))
                        except: None
                        try: product.discount = float(values[Kesia2_column_names.get('discount')].replace(',', '.'))
                        except: None  
                        try: product.net_price = float(values[Kesia2_column_names.get('net_price')].replace(',', '.'))
                        except: None
                        try: product.tva = float(values[Kesia2_column_names.get('tva')].replace(',', '.'))
                        except: None
                        try: product.net = float(values[Kesia2_column_names.get('net')].replace(',', '.'))
                        except: None

                        product.save()
                        transaction = StockTransaction.objects.create(
                            product=product,
                            quantity=product.quantity
                        )
                        transaction.save()
                        inventory_obj.products.add(product)
                        inventory_obj.transaction_list.add(transaction)
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

@login_required
def export_file(request, id=None, data_types=None, *args, **kwargs):
    inventory_obj = Inventory.objects.get(id=id)
    columns = inventory_obj.get_dtypes_as_list()
    columns.insert(0, Kesia2_column_names.get('name'))
    df = pandas.DataFrame([p.to_dict() for p in inventory_obj.products.all()], columns = columns)
    file_path = f'{settings.MEDIA_ROOT}/{inventory_obj.name}.xlsx'
    df.to_excel(file_path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404


def get_inventory_with_email(email):
    customer = Customer.get_customer_by_user_email(email)
    return Inventory.objects.get(customer=customer)