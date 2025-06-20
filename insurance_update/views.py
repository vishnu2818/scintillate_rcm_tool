from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .forms import *
from django.contrib.auth.decorators import login_required

def login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'login.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({'message': f'Hello {request.user.email}, you accessed a protected API!'})


from django.shortcuts import render
from .models import InsuranceEdit, ModifierRule, Client


def unified_dashboard(request):
    client_id = request.GET.get('client')
    payer = request.GET.get('payer')
    cpt_type = request.GET.get('cpt_type')
    cpt_code = request.GET.get('cpt_code')
    category = request.GET.get('edit_category')
    sub_category = request.GET.get('edit_sub_category')

    insurance_data = InsuranceEdit.objects.all()
    modifier_data = ModifierRule.objects.all()

    if client_id:
        insurance_data = insurance_data.filter(client_id=client_id)
        modifier_data = modifier_data.filter(client_id=client_id)
    if payer:
        insurance_data = insurance_data.filter(payer_name__icontains=payer)
    if category:
        insurance_data = insurance_data.filter(edit_type__icontains=category)
    if sub_category:
        insurance_data = insurance_data.filter(edit_sub_category__icontains=sub_category)

    context = {
        'insurance_data': insurance_data,
        'modifier_data': modifier_data,
        'clients': Client.objects.all(),
    }
    return render(request, 'dashboard.html', context)


import csv
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="insurance_edits.csv"'
    writer = csv.writer(response)
    writer.writerow(['Client', 'Payer', 'Edit Type', 'Instruction', 'Version'])

    for row in InsuranceEdit.objects.all():
        writer.writerow([row.client.name, row.payer_name, row.edit_type, row.instruction, row.version])

    return response


@login_required
def add_edit_insurance(request):
    form = InsuranceEditForm(request.POST or None)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.created_by = request.user
        instance.save()
        return redirect('dashboard')
    return render(request, 'add_edit.html', {'form': form})

import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ExcelDualUploadForm
from .models import Client, InsuranceEdit, ModifierRule
from django.contrib.auth.decorators import login_required

@login_required
def unified_excel_import_view(request):
    if request.method == 'POST':
        if 'confirm' in request.POST:
            insurance_data = request.session.get('insurance_data', [])
            modifier_data = request.session.get('modifier_data', [])

            for row in insurance_data:
                client, _ = Client.objects.get_or_create(name=row.get('client', ''))
                InsuranceEdit.objects.create(
                    client=client,
                    payer_name=row.get('payer_name', ''),
                    payer_category=row.get('payer_category', ''),
                    edit_type=row.get('edit_type', ''),
                    edit_sub_category=row.get('edit_sub_category', ''),
                    instruction=row.get('instruction', ''),
                    version=row.get('version', ''),
                    created_by=request.user
                )

            for row in modifier_data:
                client, _ = Client.objects.get_or_create(name=row.get('client', ''))
                ModifierRule.objects.create(
                    client=client,
                    payer_name=row.get('payer_name', ''),
                    payer_category=row.get('payer_category', ''),
                    code_type=row.get('code_type', ''),
                    code_list=row.get('code_list', ''),
                    sub_category=row.get('sub_category', ''),
                    modifier_instruction=row.get('modifier_instruction', ''),
                    created_by=request.user
                )

            request.session.pop('insurance_data', None)
            request.session.pop('modifier_data', None)
            messages.success(request, "Excel data imported successfully.")
            return redirect('dashboard')

        else:
            form = ExcelDualUploadForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES['excel_file']
                xl = pd.ExcelFile(excel_file)

                # Read both sheets
                df1 = xl.parse('insurance_edits')
                df2 = xl.parse('modifier_rules')

                df1.columns = [c.strip().lower().replace(' ', '_') for c in df1.columns]
                df2.columns = [c.strip().lower().replace(' ', '_') for c in df2.columns]

                insurance_data = df1.fillna('').to_dict(orient='records')
                modifier_data = df2.fillna('').to_dict(orient='records')

                request.session['insurance_data'] = insurance_data
                request.session['modifier_data'] = modifier_data

                return render(request, 'excel_preview_dual.html', {
                    'insurance_data': insurance_data[:5],
                    'modifier_data': modifier_data[:5],
                })
    else:
        form = ExcelDualUploadForm()

    return render(request, 'excel_upload_dual.html', {'form': form})
