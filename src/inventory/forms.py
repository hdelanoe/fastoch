from django import forms


class ImportForm(forms.Form):
    provider = forms.CharField(max_length=50)
    move_type = forms.RadioSelect()

    def isvalid(self):
        """Return True if the form has no errors, or False otherwise."""
        return self.is_bound and not self.errors

class QuestionForm(forms.Form):
    question = forms.CharField(label="Your question", max_length=100)
