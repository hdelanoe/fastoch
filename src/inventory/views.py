import tabula
from django.core.files.storage import FileSystemStorage

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from customers.models import Customer
from inventory.models import Inventory

@login_required
def inventory_view(request, name=None, *args, **kwargs):
    customer = Customer.get_customer_by_user_email(request.user.email)
    inventory_obj = Inventory.objects.get(customer=customer)[0]
    context = {
        "entry_list": inventory_obj.products.all(),
    }
    return render(request, "inventory/inventory.html", context) 

def upload(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_path = fs.path(filename)
        data = tabula.read_pdf(file_path)
        tabula.convert_into(
            file_path, 'test.json', output_format='json', stream=True, lattice=True, guess=True, pages='all')
        return render(request, 'upload.html', {'data': data})
        #data = tabula.read_pdf(file_path, output_format="json", lattice=True, pages='all')
        #return render(request, 'upload.html', {'data': data})
    return render(request, 'upload.html')  
