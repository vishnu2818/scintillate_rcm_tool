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
from django.apps import apps


def unified_dashboard(request):
    all_models = apps.get_models()
    model_names = [model.__name__.lower() for model in all_models if model._meta.app_label == 'insurance_update']

    return render(request, 'dashboard.html', {
        'table_list': model_names,
        'clients': Client.objects.all(),
        'insurance_data': InsuranceEdit.objects.all(),
        'modifier_data': ModifierRule.objects.all(),
    })


from django.apps import apps
from django.http import Http404
from django.shortcuts import render


def dynamic_table_view(request, model):
    try:
        Model = apps.get_model('insurance_update', model.capitalize())
    except LookupError:
        raise Http404("Model not found.")

    records = Model.objects.all()
    fields = [f.name for f in Model._meta.fields]

    return render(request, 'table_list.html', {
        'model_name': model,
        'records': records,
        'fields': fields,
    })


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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import pandas as pd
from .forms import ExcelDualUploadForm
from .models import Client, InsuranceEdit, ModifierRule

INSURANCE_HEADER_MAP = {
    'PAYERS': 'payer_name',
    'Payor Category': 'payer_category',
    'EDITS Category': 'edit_type',
    'EDITS Sub-Category': 'edit_sub_category',
    'EDITS - Instructions': 'instruction'
}

MODIFIER_HEADER_MAP = {
    'PAYERS': 'payer_name',
    'Payor Category': 'payer_category',
    'CPT Code Type': 'code_type',
    'CPT Code Selection': 'code_list',
    'CPT Sub-Category': 'sub_category',
    'CPT Based Modifier Instruction': 'modifier_instruction'
}


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

                sheet_names = xl.sheet_names
                df1, df2 = None, None

                for sheet_name in sheet_names:
                    df = xl.parse(sheet_name)
                    df.columns = [col.strip() for col in df.columns]

                    if set(INSURANCE_HEADER_MAP.keys()).issubset(df.columns):
                        df1 = df.copy()
                    elif set(MODIFIER_HEADER_MAP.keys()).issubset(df.columns):
                        df2 = df.copy()

                if df1 is None or df2 is None:
                    messages.error(request, "Excel file must contain both sheets with correct headers.")
                    return redirect('excel_import')

                # Rename using auto-mapping
                df1.rename(columns=INSURANCE_HEADER_MAP, inplace=True)
                df2.rename(columns=MODIFIER_HEADER_MAP, inplace=True)

                df1['client'] = 'Default Client'
                df1['version'] = 'v1.0'
                df2['client'] = 'Default Client'

                insurance_data = df1.fillna('').to_dict(orient='records')
                modifier_data = df2.fillna('').to_dict(orient='records')

                request.session['insurance_data'] = insurance_data
                request.session['modifier_data'] = modifier_data

                return render(request, 'excel_preview_dual.html', {
                    'insurance_headers': list(df1.columns),
                    'modifier_headers': list(df2.columns),
                    'insurance_field_options': ['payer_name', 'payer_category', 'edit_type', 'edit_sub_category',
                                                'instruction'],
                    'modifier_field_options': ['payer_name', 'payer_category', 'code_type', 'code_list', 'sub_category',
                                               'modifier_instruction'],
                })
    else:
        form = ExcelDualUploadForm()

    return render(request, 'excel_upload_dual.html', {'form': form})


from django.shortcuts import render, redirect
from django.apps import apps
from django.contrib.auth import get_user_model
from .models import ModelAccessPermission

User = get_user_model()


def manage_permissions(request):
    app_label = 'insurance_update'  # Change to your app name
    actions = ['read', 'add', 'edit', 'delete']

    models = []
    for model in apps.get_models():
        if model._meta.app_label == app_label:
            models.append({
                'object': model,
                'name': model.__name__,
                'key': model.__name__.lower()
            })

    users = User.objects.all()

    if request.method == 'POST':
        for model in models:
            for user in users:
                key = f"{model['key']}_{user.id}"

                can_view = bool(request.POST.get(f"{key}_read"))
                can_add = bool(request.POST.get(f"{key}_add"))
                can_edit = bool(request.POST.get(f"{key}_edit"))
                can_delete = bool(request.POST.get(f"{key}_delete"))

                ModelAccessPermission.objects.update_or_create(
                    user=user,
                    model_name=model['name'],
                    defaults={
                        'can_view': can_view,
                        'can_add': can_add,
                        'can_edit': can_edit,
                        'can_delete': can_delete,
                    }
                )
        return redirect('manage_permissions')

    permissions = ModelAccessPermission.objects.all()
    permission_map = {
        f"{perm.model_name.lower()}_{perm.user.id}": perm for perm in permissions
    }

    return render(request, 'admin_permissions.html', {
        'models': models,
        'users': users,
        'actions': actions,
        'permission_map': permission_map,
    })


from .models import InsuranceEdit, ModifierRule, Client
from django.db.models import Q


def model_tables_view(request):
    # Filters for InsuranceEdit
    insurance_filter = Q()
    client_id = request.GET.get('client', '').strip()
    if client_id:
        insurance_filter &= Q(client__id=client_id)
    if 'payer_name' in request.GET:
        insurance_filter &= Q(payer_name=request.GET['payer_name'])
    if 'payer_category' in request.GET:
        insurance_filter &= Q(payer_category=request.GET['payer_category'])
    if 'edit_type' in request.GET:
        insurance_filter &= Q(edit_type=request.GET['edit_type'])
    if 'edit_sub_category' in request.GET:
        insurance_filter &= Q(edit_sub_category=request.GET['edit_sub_category'])

    insurance_edits = InsuranceEdit.objects.filter(insurance_filter)

    # Dropdown options
    clients = Client.objects.all()
    payer_names = InsuranceEdit.objects.values_list('payer_name', flat=True).distinct()
    payer_categories = InsuranceEdit.objects.values_list('payer_category', flat=True).distinct()
    edit_types = InsuranceEdit.objects.values_list('edit_type', flat=True).distinct()
    edit_sub_categories = InsuranceEdit.objects.values_list('edit_sub_category', flat=True).distinct()

    # ModifierRule filter
    modifier_rules = ModifierRule.objects.all()
    if 'code_list' in request.GET:
        modifier_rules = modifier_rules.filter(code_list__icontains=request.GET['code_list'])

    return render(request, 'model_tables.html', {
        'insurance_edits': insurance_edits,
        'modifier_rules': modifier_rules,
        'clients': clients,
        'payer_names': payer_names,
        'payer_categories': payer_categories,
        'edit_types': edit_types,
        'edit_sub_categories': edit_sub_categories,
        'filters': request.GET,
    })
