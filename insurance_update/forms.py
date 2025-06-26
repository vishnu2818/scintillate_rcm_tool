from django import forms
from .models import *


class InsuranceEditForm(forms.ModelForm):
    class Meta:
        model = InsuranceEdit
        fields = ['payer_name', 'payer_category', 'edit_type', 'edit_sub_category', 'instruction']
        widgets = {
            'instruction': forms.Textarea(attrs={'rows': 3}),
        }


class ExcelDualUploadForm(forms.Form):
    # excel_file = forms.FileField(label="Upload Excel v2.2 File")
    excel_file = forms.FileField(
        label="Choose Excel File",
        widget=forms.ClearableFileInput(attrs={
            'class': 'block w-full text-sm text-gray-700 border border-gray-300 rounded-md p-2 cursor-pointer',
            'accept': '.xls,.xlsx'  # Restrict to Excel file types
        })
    )


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 p-2 border rounded w-full',
                'placeholder': 'Enter client name',
                'id': 'clientName'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4',
                'id': 'clientActive'
            }),
        }