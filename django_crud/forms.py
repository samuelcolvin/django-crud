from django import forms


class RichCrudForm(forms.ModelForm):
    class Media:
        css = {
            'all': ('crud/forms.css',)
        }
