from django import forms
from .models import InsuranceEdit


class InsuranceEditForm(forms.ModelForm):
    class Meta:
        model = InsuranceEdit
        fields = ['client', 'payer_name', 'payer_category', 'edit_type', 'edit_sub_category', 'instruction', 'version']


class ExcelDualUploadForm(forms.Form):
    excel_file = forms.FileField(label="Upload Excel v2.2 File")
