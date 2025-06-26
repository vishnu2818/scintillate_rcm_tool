from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .forms import *
from django.contrib.auth import authenticate, login
from .models import *
import csv
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
import pandas as pd
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.apps import apps
from django.http import Http404
from django.db.models import Q


def login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)

            # ✅ Log the login activity
            ActivityLog.objects.create(
                user=user,
                action="Login",
                target_type="User",
                target_id=user.id,
                details="User logged in successfully"
            )

            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'login.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({'message': f'Hello {request.user.email}, you accessed a protected API!'})


def unified_dashboard(request):
    all_models = apps.get_models()
    model_names = [model.__name__.lower() for model in all_models if model._meta.app_label == 'insurance_update']

    return render(request, 'dashboard.html', {
        'table_list': model_names,
        'clients': Client.objects.all(),
        'insurance_data': InsuranceEdit.objects.all(),
        'modifier_data': ModifierRule.objects.all(),
    })


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

            # ✅ Log the import activity
            ActivityLog.objects.create(
                user=request.user,
                action="Import",
                target_type="Excel",
                target_id=request.user.id,
                details="User imported Excel data successfully"
            )

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


User = get_user_model()


def manage_permissions(request):
    app_label = 'insurance_update'
    actions = ['read', 'add', 'edit', 'delete']

    # ✅ Get all models in app and assign lowercase key
    models = [
        {'object': model, 'name': model.__name__, 'key': model.__name__.lower()}
        for model in apps.get_models()
        if model._meta.app_label == app_label
    ]

    users = User.objects.all()

    if request.method == 'POST':
        form_keys = set(request.POST.keys())
        print("💡 Received form keys:", form_keys)

        updated = 0

        for model in models:
            for user in users:
                prefix = f"{model['key']}_{user.id}"

                read_key = f"{prefix}_read"
                add_key = f"{prefix}_add"
                edit_key = f"{prefix}_edit"
                delete_key = f"{prefix}_delete"

                if not any(k in form_keys for k in [read_key, add_key, edit_key, delete_key]):
                    continue

                perm, created = ModelAccessPermission.objects.get_or_create(
                    user=user,
                    model_name=model['name']
                )
                perm.can_view = read_key in form_keys
                perm.can_add = add_key in form_keys
                perm.can_edit = edit_key in form_keys
                perm.can_delete = delete_key in form_keys
                perm.save()

                updated += 1
                print(f"{'Created' if created else 'Updated'} permission for {user.email} on {model['name']}")

        messages.success(request, f"✅ {updated} permissions updated.")
        # ✅ Log the permission change activity
        ActivityLog.objects.create(
            user=request.user,
            action="Permission Update",
            target_type="Permission",
            target_id=request.user.id,
            details="User updated access permissions."
        )
        return redirect('manage_permissions')

    # ✅ Load current saved permission map
    permission_map = {
        f"{p.model_name.lower()}_{p.user.id}": p
        for p in ModelAccessPermission.objects.all()
    }

    return render(request, 'admin_permissions.html', {
        'models': models,
        'users': users,
        'actions': actions,
        'permission_map': permission_map,
    })


def model_tables_view(request):
    # Filters for InsuranceEdit
    insurance_filter = Q()

    client_id = request.GET.get('client', '').strip()
    if client_id:
        insurance_filter &= Q(client__id=client_id)

    payer_name = request.GET.get('payer_name', '').strip()
    if payer_name:
        insurance_filter &= Q(payer_name=payer_name)

    payer_category = request.GET.get('payer_category', '').strip()
    if payer_category:
        insurance_filter &= Q(payer_category=payer_category)

    edit_type = request.GET.get('edit_type', '')
    if edit_type:
        insurance_filter &= Q(edit_type__icontains=edit_type.strip())

    edit_sub_category = request.GET.get('edit_sub_category', '').strip()
    if edit_sub_category:
        insurance_filter &= Q(edit_sub_category=edit_sub_category)

    # Apply filter only if filters are valid, else return all
    if insurance_filter:
        insurance_edits = InsuranceEdit.objects.filter(insurance_filter)
    else:
        insurance_edits = InsuranceEdit.objects.all()

    # Dropdown options
    clients = Client.objects.all()
    payer_names = InsuranceEdit.objects.values_list('payer_name', flat=True).distinct()
    payer_categories = InsuranceEdit.objects.values_list('payer_category', flat=True).distinct()
    edit_types = InsuranceEdit.objects.values_list('edit_type', flat=True).distinct()
    edit_sub_categories = InsuranceEdit.objects.values_list('edit_sub_category', flat=True).distinct()

    # # ModifierRule Filter
    # modifier_rules = ModifierRule.objects.all()
    # code_list_filter = request.GET.get('code_list', '').strip()
    # if code_list_filter:
    #     modifier_rules = modifier_rules.filter(code_list__icontains=code_list_filter)

    # ModifierRule Filters
    mod_filter = Q()

    # Dropdown filters
    mod_payer_name = request.GET.get('payer_name', '')
    mod_payer_category = request.GET.get('payer_category', '')
    code_type = request.GET.get('code_type', '')

    if mod_payer_name:
        mod_filter &= Q(payer_name=mod_payer_name)
    if mod_payer_category:
        mod_filter &= Q(payer_category=mod_payer_category)
    if code_type:
        mod_filter &= Q(code_type=code_type)

    # Search filters
    code_list = request.GET.get('code_list', '')
    sub_category = request.GET.get('sub_category', '')

    if code_list:
        mod_filter &= Q(code_list__icontains=code_list)
    if sub_category:
        mod_filter &= Q(sub_category__icontains=sub_category)

    # Fetch filtered results
    modifier_rules = ModifierRule.objects.filter(mod_filter)

    # For dropdowns
    mod_payer_names = ModifierRule.objects.values_list('payer_name', flat=True).distinct()
    mod_payer_categories = ModifierRule.objects.values_list('payer_category', flat=True).distinct()
    code_types = ModifierRule.objects.values_list('code_type', flat=True).distinct()

    # Client filters
    client_filter = Q()
    name = request.GET.get('client_name', '').strip()
    active = request.GET.get('active', '').strip()

    if name:
        client_filter &= Q(name__icontains=name)

    if active == 'true':
        client_filter &= Q(active=True)
    elif active == 'false':
        client_filter &= Q(active=False)

    clients = Client.objects.filter(client_filter)

    # activity_logs = ActivityLog.objects.select_related('user').order_by('-timestamp')[:100]
    activity_logs = ActivityLog.objects.order_by('-timestamp')[:100]

    return render(request, 'model_tables.html', {
        'insurance_edits': insurance_edits,
        'clients': clients,
        'payer_names': payer_names,
        'payer_categories': payer_categories,
        'edit_types': edit_types,
        'edit_sub_categories': edit_sub_categories,
        'filters': request.GET,

        'modifier_rules': modifier_rules,
        'mod_payer_names': mod_payer_names,
        'mod_payer_categories': mod_payer_categories,
        'code_types': code_types,
        'activity_logs': activity_logs,
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import InsuranceEdit
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@require_http_methods(["POST"])
def insurance_create(request):

    client, _ = Client.objects.get_or_create(name='Default Client')
    payer_name = request.POST.get('payer_name')
    insurance = InsuranceEdit.objects.create(
        client=client,
        payer_name=payer_name,
        payer_category=request.POST.get('payer_category'),
        edit_type=request.POST.get('edit_type'),
        edit_sub_category=request.POST.get('edit_sub_category'),
        version='v1.0',
        instruction=request.POST.get('instruction'),
        created_by=request.user
    )

    # ✅ Log the creation
    ActivityLog.objects.create(
        user=request.user,
        action="Create",
        target_type="InsuranceEdit",
        target_id=insurance.id,
        details=f"Created insurance: {payer_name}"
    )
    return JsonResponse({'success': True})


def insurance_edit(request, pk):
    insurance = get_object_or_404(InsuranceEdit, pk=pk)
    if request.method == 'POST':
        insurance.payer_name = request.POST.get('payer_name')
        insurance.payer_category = request.POST.get('payer_category')
        insurance.edit_type = request.POST.get('edit_type')
        insurance.edit_sub_category = request.POST.get('edit_sub_category')
        # insurance.version = request.POST.get('version')
        insurance.instruction = request.POST.get('instruction')
        insurance.save()

        # ✅ Log the update
        ActivityLog.objects.create(
            user=request.user,
            action="Edit",
            target_type="InsuranceEdit",
            target_id=insurance.id,
            details=f"Edited insurance: {insurance.payer_name}"
        )

        return redirect('model_tables')
    return JsonResponse({
        'id': insurance.id,
        'payer_name': insurance.payer_name,
        'payer_category': insurance.payer_category,
        'edit_type': insurance.edit_type,
        'edit_sub_category': insurance.edit_sub_category,
        # 'version': insurance.version,
        'instruction': insurance.instruction,
    })


@csrf_exempt
def insurance_delete(request, pk):
    insurance = get_object_or_404(InsuranceEdit, pk=pk)
    insurance_name = insurance.payer_name
    insurance_id = insurance.id
    insurance.delete()

    # ✅ Log the deletion
    ActivityLog.objects.create(
        user=request.user,
        action="Delete",
        target_type="InsuranceEdit",
        target_id=insurance_id,
        details=f"Deleted insurance: {insurance_name}"
    )

    return JsonResponse({'status': 'deleted'})


# views.py

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from .models import ModifierRule


@login_required
@require_POST
def modifier_create(request):
    """
    Handle AJAX POST to create a new ModifierRule.
    Expects payer_name, payer_category, code_type, code_list, sub_category, modifier_instruction.
    """
    client, _ = Client.objects.get_or_create(name='Default Client')
    rule = ModifierRule.objects.create(
        client=client,
        payer_name=request.POST.get('payer_name', ''),
        payer_category=request.POST.get('payer_category', ''),
        code_type=request.POST.get('code_type', ''),
        code_list=request.POST.get('code_list', ''),
        sub_category=request.POST.get('sub_category', ''),
        modifier_instruction=request.POST.get('modifier_instruction', ''),
        created_by=request.user
    )

    # ✅ Log creation
    ActivityLog.objects.create(
        user=request.user,
        action="Create",
        target_type="ModifierRule",
        target_id=rule.id,
        details=f"Created modifier for payer: {rule.payer_name}"
    )

    return JsonResponse({'success': True, 'id': rule.id})


@login_required
@require_http_methods(["GET", "POST"])
def modifier_edit(request, pk):
    """
    GET: Return JSON of existing ModifierRule (for populating the edit form).
    POST: Update the ModifierRule and return success JSON.
    """
    rule = get_object_or_404(ModifierRule, pk=pk)

    if request.method == 'GET':
        return JsonResponse({
            'id': rule.id,
            'payer_name': rule.payer_name,
            'payer_category': rule.payer_category,
            'code_type': rule.code_type,
            'code_list': rule.code_list,
            'sub_category': rule.sub_category,
            'modifier_instruction': rule.modifier_instruction,
        })

    # POST → update
    rule.payer_name = request.POST.get('payer_name', rule.payer_name)
    rule.payer_category = request.POST.get('payer_category', rule.payer_category)
    rule.code_type = request.POST.get('code_type', rule.code_type)
    rule.code_list = request.POST.get('code_list', rule.code_list)
    rule.sub_category = request.POST.get('sub_category', rule.sub_category)
    rule.modifier_instruction = request.POST.get('modifier_instruction', rule.modifier_instruction)
    rule.save()

    # ✅ Log edit
    ActivityLog.objects.create(
        user=request.user,
        action="Edit",
        target_type="ModifierRule",
        target_id=rule.id,
        details=f"Edited modifier for payer: {rule.payer_name}"
    )

    return JsonResponse({'success': True})


@login_required
@require_POST
def modifier_delete(request, pk):
    """
    Handle AJAX POST to delete a ModifierRule.
    """
    rule = get_object_or_404(ModifierRule, pk=pk)
    rule_id = rule.id
    payer_name = rule.payer_name
    rule.delete()

    # ✅ Log delete
    ActivityLog.objects.create(
        user=request.user,
        action="Delete",
        target_type="ModifierRule",
        target_id=rule_id,
        details=f"Deleted modifier for payer: {payer_name}"
    )

    return JsonResponse({'success': True})


from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from .models import Client


@login_required
@require_POST
def client_create(request):
    name = request.POST.get('name', '').strip()
    active = request.POST.get('active') == 'true'

    if not name:
        return JsonResponse({'success': False, 'error': 'Client name is required'}, status=400)

    client = Client.objects.create(name=name, active=active)
    # ✅ Log the creation
    ActivityLog.objects.create(
        user=request.user,
        action="Create",
        target_type="Client",
        target_id=client.id,
        details=f"Created client: {client.name}"
    )
    return JsonResponse({'success': True, 'id': client.id})


@login_required
@require_http_methods(["GET", "POST"])
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'GET':
        return JsonResponse({
            'id': client.id,
            'name': client.name,
            'active': client.active,
        })

    name = request.POST.get('name', '').strip()
    active = request.POST.get('active') == 'true'

    if not name:
        return JsonResponse({'success': False, 'error': 'Client name is required'}, status=400)

    client.name = name
    client.active = active
    client.save()

    # ✅ Log the edit
    ActivityLog.objects.create(
        user=request.user,
        action="Edit",
        target_type="Client",
        target_id=client.id,
        details=f"Updated client: {client.name}"
    )

    return JsonResponse({'success': True})



@login_required
@require_POST
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    client_id = client.id
    client_name = client.name
    client.delete()

    # ✅ Log the deletion
    ActivityLog.objects.create(
        user=request.user,
        action="Delete",
        target_type="Client",
        target_id=client_id,
        details=f"Deleted client: {client_name}"
    )

    return JsonResponse({'success': True})
