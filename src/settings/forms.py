from django import forms


class SettingsForm(forms.Form):
    erase = forms.BooleanField()

    def isvalid(self):
        """Return True if the form has no errors, or False otherwise."""
        return self.is_bound and not self.errors
    
