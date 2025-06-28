from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from collections import defaultdict
from .check_permission import check_model_permission
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
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import get_user_model
from .models import ModelAccessPermission, ActivityLog
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import InsuranceEdit
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from .models import Client
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from .models import ModifierRule


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


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.apps import apps
from .models import InsuranceEdit, ModifierRule, Client, ActivityLog, ModelAccessPermission

@login_required
def unified_dashboard(request):
    all_models = apps.get_models()
    model_names = [model.__name__.lower() for model in all_models if model._meta.app_label == 'insurance_update']

    insurance_count = InsuranceEdit.objects.count()
    modifier_count = ModifierRule.objects.count()
    client_count = Client.objects.count()
    dxcategory_count = DxCategory.objects.count()
    scenario_count = Scenario.objects.count()

    # ActivityLog counts
    create_count = ActivityLog.objects.filter(action="Create").count()
    edit_count = ActivityLog.objects.filter(action="Edit").count()
    delete_count = ActivityLog.objects.filter(action="Delete").count()
    total_activity = create_count + edit_count + delete_count or 1

    create_pct = round((create_count / total_activity) * 100, 2)
    edit_pct = round((edit_count / total_activity) * 100, 2)
    delete_pct = round((delete_count / total_activity) * 100, 2)

    stat_cards = [
        {'title': 'Insurance Edits', 'icon': 'https://cdn.lordicon.com/vduvxizq.json', 'color': 'blue',
         'count': insurance_count},
        {'title': 'Modifier Rules', 'icon': 'https://cdn.lordicon.com/egmlnyku.json', 'color': 'purple',
         'count': modifier_count},
        {'title': 'Clients', 'icon': 'https://cdn.lordicon.com/kthelypq.json', 'color': 'green', 'count': client_count},
        {'title': 'Scenario Records', 'icon': 'https://cdn.lordicon.com/egiwmiit.json', 'color': 'indigo',
         'count': scenario_count},
        {'title': 'Dx Categories', 'icon': 'https://cdn.lordicon.com/qvyppzqz.json', 'color': 'cyan',
         'count': dxcategory_count},
    ]

    activity_chart = [
        {'label': 'Create', 'pct': create_pct, 'color': 'green', 'emoji': '🟢'},
        {'label': 'Edit', 'pct': edit_pct, 'color': 'blue', 'emoji': '🔵'},
        {'label': 'Delete', 'pct': delete_pct, 'color': 'red', 'emoji': '🔴'},
    ]

    return render(request, 'dashboard.html', {
        'stat_cards': stat_cards,
        'activity_chart': activity_chart,
        'user': request.user,
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
            return render(request, 'import_success.html')
            # return redirect('dashboard')

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

    models = [
        {'object': model, 'name': model.__name__, 'key': model.__name__.lower()}
        for model in apps.get_models()
        if model._meta.app_label == app_label
    ]

    users = User.objects.all()

    if request.method == 'POST':
        form_keys = set(request.POST.keys())
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

        messages.success(request, f"✅ {updated} permission records updated.")
        ActivityLog.objects.create(
            user=request.user,
            action="Permission Update",
            target_type="Permission",
            target_id=request.user.id,
            details="User updated model-level access permissions."
        )
        return redirect(f'{request.path}?selected_user={request.POST.get("selected_user")}')

    permission_map = {
        f"{p.model_name.lower()}_{p.user.id}": p
        for p in ModelAccessPermission.objects.all()
    }

    js_permission_data = {
        key: {
            'can_view': perm.can_view,
            'can_add': perm.can_add,
            'can_edit': perm.can_edit,
            'can_delete': perm.can_delete,
        } for key, perm in permission_map.items()
    }

    selected_user = request.GET.get("selected_user", "")

    return render(request, 'admin_permissions.html', {
        'models': models,
        'users': users,
        'actions': actions,
        'permission_map': permission_map,
        'js_permission_data': json.dumps(js_permission_data, cls=DjangoJSONEncoder),
        'selected_user': selected_user,
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
    users = User.objects.select_related('client').order_by('role')

    grouped_insurance_edits = defaultdict(list)
    for edit in insurance_edits:
        key = f"{edit.payer_name}__{edit.payer_category}"
        grouped_insurance_edits[key].append(edit)

    grouped_insurance = defaultdict(list)
    for edit in insurance_edits:
        key = f"{edit.payer_name}__{edit.payer_category}"
        grouped_insurance[key].append(edit)

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

        'scenario_data': Scenario.objects.all(),
        'dxcategory_data': DxCategory.objects.all(),
        'users': users
    })


@csrf_exempt
def user_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        role = request.POST.get("role")
        client_id = request.POST.get("client")
        active = request.POST.get("active") == "true"

        # 💡 Check for existing user with the same email
        if User.objects.filter(email=email).exists():
            return JsonResponse({"success": False, "message": "User with this email already exists."}, status=400)

        client = Client.objects.filter(id=client_id).first() if client_id else None

        user = User.objects.create_user(email=email, name=name, password="default123", role=role, client=client)
        user.is_active = active
        user.save()

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)


@csrf_exempt
def user_edit(request, pk):
    user = User.objects.get(pk=pk)
    if request.method == "GET":
        return JsonResponse({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "client_id": user.client.id if user.client else "",
            "is_active": user.is_active
        })

    if request.method == "POST":
        user.name = request.POST.get("name")
        user.email = request.POST.get("email")
        user.role = request.POST.get("role")
        client_id = request.POST.get("client")
        user.client = Client.objects.filter(id=client_id).first() if client_id else None
        user.is_active = request.POST.get("active") == "true"
        user.save()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400)

@csrf_exempt
def user_delete(request, pk):
    if request.method == "POST":
        user = User.objects.filter(pk=pk).first()
        if user:
            user.delete()
            return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)



@login_required
@check_model_permission("InsuranceEdit", "add")
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


@check_model_permission("InsuranceEdit", "edit")
@login_required
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


@check_model_permission(("InsuranceEdit", "delete"),)
@login_required
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


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import DxCategory, ActivityLog


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def dxcategory_create(request):
    try:
        data = request.POST
        dx = DxCategory.objects.create(
            dxcategory_id=data.get('dxcategory_id'),
            dxcategory_code=data.get('code'),
            dxcategory_category=data.get('category'),
            dxcategory_sub_category=data.get('sub_category'),
            dxcategory_type=data.get('type'),
            dxcategory_instructions=data.get('instructions'),
            dxcategory_sow_id=data.get('sow_id')
        )

        # ✅ Log
        ActivityLog.objects.create(
            user=request.user,
            action="Create",
            target_type="DxCategory",
            target_id=dx.id,
            details=f"Created DxCategory: {dx.dxcategory_code} (External ID: {dx.dxcategory_id})"
        )

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET", "POST"])
def dxcategory_edit(request, id):
    try:
        dx = DxCategory.objects.get(id=id)

        if request.method == "GET":
            return JsonResponse({
                'id': dx.id,
                'dxcategory_id': dx.dxcategory_id,
                'code': dx.dxcategory_code,
                'category': dx.dxcategory_category,
                'sub_category': dx.dxcategory_sub_category,
                'type': dx.dxcategory_type,
                'instructions': dx.dxcategory_instructions,
                'sow_id': dx.dxcategory_sow_id,
            })

        elif request.method == "POST":
            data = request.POST
            dx.dxcategory_id = data.get('dxcategory_id')
            dx.dxcategory_code = data.get('code')
            dx.dxcategory_category = data.get('category')
            dx.dxcategory_sub_category = data.get('sub_category')
            dx.dxcategory_type = data.get('type')
            dx.dxcategory_instructions = data.get('instructions')
            dx.dxcategory_sow_id = data.get('sow_id')
            dx.save()

            # ✅ Log
            ActivityLog.objects.create(
                user=request.user,
                action="Edit",
                target_type="DxCategory",
                target_id=dx.id,
                details=f"Updated DxCategory: {dx.dxcategory_code} (External ID: {dx.dxcategory_id})"
            )

            return JsonResponse({'success': True})

    except DxCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'DxCategory not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def dxcategory_delete(request, id):
    try:
        dx = DxCategory.objects.get(id=id)
        external_id = dx.dxcategory_id
        code = dx.dxcategory_code
        dx.delete()

        # ✅ Log
        ActivityLog.objects.create(
            user=request.user,
            action="Delete",
            target_type="DxCategory",
            target_id=id,
            details=f"Deleted DxCategory: {code} (External ID: {external_id})"
        )

        return JsonResponse({'success': True})

    except DxCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'DxCategory not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import Scenario, ActivityLog

@csrf_exempt
def scenario_create(request):
    if request.method == "POST":
        try:
            scenario = Scenario.objects.create(
                scenario_id=request.POST.get("scenario_id"),
                scenario_code=request.POST.get("code"),
                scenario_category=request.POST.get("category"),
                scenario_sub_category=request.POST.get("sub_category"),
                scenario_type=request.POST.get("type"),
                scenario_instructions=request.POST.get("instructions"),
                scenario_sow_id=request.POST.get("sow_id"),
            )

            # ✅ Log creation
            ActivityLog.objects.create(
                user=request.user,
                action="Create",
                target_type="Scenario",
                target_id=scenario.id,
                details=f"Created Scenario: {scenario.scenario_code}"
            )

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return HttpResponseBadRequest("Invalid method")

@csrf_exempt
def scenario_edit(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    if request.method == "GET":
        return JsonResponse({
            "id": scenario.id,
            "scenario_id": scenario.scenario_id,
            "code": scenario.scenario_code,
            "category": scenario.scenario_category,
            "sub_category": scenario.scenario_sub_category,
            "type": scenario.scenario_type,
            "instructions": scenario.scenario_instructions,
            "sow_id": scenario.scenario_sow_id,
        })

    elif request.method == "POST":
        try:
            scenario.scenario_id = request.POST.get("scenario_id")
            scenario.scenario_code = request.POST.get("code")
            scenario.scenario_category = request.POST.get("category")
            scenario.scenario_sub_category = request.POST.get("sub_category")
            scenario.scenario_type = request.POST.get("type")
            scenario.scenario_instructions = request.POST.get("instructions")
            scenario.scenario_sow_id = request.POST.get("sow_id")
            scenario.save()

            # ✅ Log update
            ActivityLog.objects.create(
                user=request.user,
                action="Edit",
                target_type="Scenario",
                target_id=scenario.id,
                details=f"Updated Scenario: {scenario.scenario_code}"
            )

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return HttpResponseBadRequest("Invalid method")

@csrf_exempt
def scenario_delete(request, pk):
    if request.method == "POST":
        scenario = get_object_or_404(Scenario, pk=pk)
        code = scenario.scenario_code
        scenario.delete()

        # ✅ Log delete
        ActivityLog.objects.create(
            user=request.user,
            action="Delete",
            target_type="Scenario",
            target_id=pk,
            details=f"Deleted Scenario: {code}"
        )

        return JsonResponse({"success": True})

    return HttpResponseBadRequest("Invalid method")
