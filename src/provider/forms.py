from django import forms

class ProviderForm(forms.Form):
    name = forms.CharField(max_length=50)    
    n_tva = forms.CharField(max_length=13)    
    tva = forms.FloatField()  