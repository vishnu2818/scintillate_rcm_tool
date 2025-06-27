# from functools import wraps
# from django.shortcuts import redirect, render
# from .models import ModelAccessPermission
#
#
# def check_model_permission(*model_permission_pairs):
#     """
#     Example usage:
#     @check_model_permission(("InsuranceEdit", "view"), ("ModifierRule", "edit"))
#     """
#
#     def decorator(view_func):
#         @wraps(view_func)
#         def _wrapped_view(request, *args, **kwargs):
#             user = request.user
#             if user.is_superuser or user.role == 'admin':
#                 return view_func(request, *args, **kwargs)
#
#             for model_name, permission_type in model_permission_pairs:
#                 try:
#                     perm = ModelAccessPermission.objects.get(user=user, model_name=model_name)
#                     if (
#                             (permission_type == 'view' and perm.can_view) or
#                             (permission_type == 'add' and perm.can_add) or
#                             (permission_type == 'edit' and perm.can_edit) or
#                             (permission_type == 'delete' and perm.can_delete)
#                     ):
#                         continue  # permission granted for this model-action
#                     else:
#                         return render(request, "403.html", status=403)
#                 except ModelAccessPermission.DoesNotExist:
#                     return render(request, "403.html", status=403)
#
#             return view_func(request, *args, **kwargs)
#
#         return _wrapped_view
#
#     return decorator


from functools import wraps
from django.shortcuts import render
from .models import ModelAccessPermission


def check_model_permission(*model_permission_pairs):
    """
    Example usage:
    @check_model_permissions(
        ("InsuranceEdit", "view"),
        ("InsuranceEdit1", "edit"),
        ("InsuranceEdit2", "delete")
    )
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if user.is_superuser or user.role == 'admin':
                return view_func(request, *args, **kwargs)

            for model_name, permission_type in model_permission_pairs:
                try:
                    perm = ModelAccessPermission.objects.get(user=user, model_name=model_name)
                    if (
                            permission_type == 'view' and perm.can_view or
                            permission_type == 'add' and perm.can_add or
                            permission_type == 'edit' and perm.can_edit or
                            permission_type == 'delete' and perm.can_delete
                    ):
                        continue  # Permission granted for this model
                    else:
                        return render(request, "403.html", status=403)
                except ModelAccessPermission.DoesNotExist:
                    return render(request, "403.html", status=403)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
