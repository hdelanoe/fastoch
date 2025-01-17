from django import forms


class AddiProductForm(forms.Form):
    multicode = forms.CharField(max_length=16)
    ean = forms.IntegerField()
    description = forms.CharField(max_length=64)
    quantity = forms.IntegerField()
    achat_ht = forms.FloatField()

    def isvalid(self):
        """Return True if the form has no errors, or False otherwise."""
        return self.is_bound and not self.errors