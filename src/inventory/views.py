import pandas
import camelot
from django.core.files.storage import FileSystemStorage

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from customers.models import Customer
from inventory.models import Inventory

@login_required
def inventory_view(request, name=None, confirm_inventory=False, *args, **kwargs):
    customer = Customer.get_customer_by_user_email(request.user.email)
    inventory_obj = Inventory.objects.get(customer=customer)
    context = {
        "entry_list": inventory_obj.products.all(),
        "inventory_list": [inventory_obj],
        "inventory_name": inventory_obj.name,

    }
    return render(request, "inventory/inventory.html", context) 

@login_required
def upload_file(request, name=None, *args, **kwargs):
    if request.method == 'POST':
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
            
            # get columns
            parse_columns = df.values[0]
            
            data_df = pandas.DataFrame(data=None, columns = parse_columns)
            df = df.drop([0])
            for x in range(len(df.index)):
                data_df.loc[x] = df.values[x]
            data_df.dropna(axis=1, inplace=True)
            #data_df.replace('', numpy.nan, inplace=True)
            #data_df.dropna(axis=0, inplace=True)

            print(data_df.dtypes)
            print(data_df)
        except:
            None
        fs.delete(file_path)
    return inventory_view(request, name, True)
