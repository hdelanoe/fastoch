from django import forms

class ProviderForm(forms.Form):
    name = forms.CharField(max_length=32)  
    code = forms.CharField(max_length=4)  
    erase_multicode = forms.BooleanField(required=False) 