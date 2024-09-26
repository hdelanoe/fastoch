from django import forms


class FileForm(forms.Form):
    file = forms.FileField()

    def isvalid(self):
        """Return True if the form has no errors, or False otherwise."""
        return self.is_bound and not self.errors

class QuestionForm(forms.Form):
    question = forms.CharField(label="Your question", max_length=100)

class ProductForm(forms.Form):
    description = forms.CharField(max_length=50)    