from django import forms


class FileForm(forms.Form):
    file = forms.FileField()

    def isvalid(self):
        """Return True if the form has no errors, or False otherwise."""
        return self.is_bound and not self.errors

class QuestionForm(forms.Form):
    question = forms.CharField(label="Your question", max_length=100)

class ProductForm(forms.Form):
    fournisseur = forms.CharField(max_length=50)    
    description = forms.CharField(max_length=50)    
    price_net = forms.FloatField()    
    price_tva = forms.FloatField()    