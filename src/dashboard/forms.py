from django import forms


class NameForm(forms.Form):
    your_name = forms.CharField(label="Your name", max_length=100)

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()