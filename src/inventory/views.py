import tabula
from django.shortcuts import render




from django.core.files.storage import FileSystemStorage

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
