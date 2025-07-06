# from .views import *
# from .check_permission import check_model_permission
# from django.urls import path
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# from django.contrib.auth.views import LogoutView
#
#
# urlpatterns = [
#     path('', login_page, name='login_page'),
#     path('logout/', LogoutView.as_view(next_page='login_page'), name='logout'),
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('api/protected/', protected_view, name='protected_view'),
#     path('export/', export_csv, name='export_csv'),
#     # path('add-edit/', add_edit_insurance, name='add_edit_insurance'),
#     path('import/excel/', unified_excel_import_view, name='excel_import'),
#
#     # path('table/<str:model>/', dynamic_table_view, name='table_view'),
#     path('permissions/', manage_permissions, name='manage_permissions'),
#     path('model-tables/', model_tables_view, name='model_tables'),
#
#
#
#     path('dashboard/', unified_dashboard, name='dashboard'),
#
#     # ✅ Restrict Permissions
#     path('permissions/', check_model_permission('ModelAccessPermission', 'view')(manage_permissions), name='manage_permissions'),
#
#     # ✅ Insurance
#     path('insurance/create/', check_model_permission('InsuranceEdit', 'add')(insurance_create), name='insurance_create'),
#     path('insurance/edit/<int:pk>/', check_model_permission('InsuranceEdit', 'edit')(insurance_edit), name='insurance_edit'),
#     path('insurance/delete/<int:pk>/', check_model_permission('InsuranceEdit', 'delete')(insurance_delete), name='insurance_delete'),
#
#     # ✅ Modifier
#     path('modifier/create/', check_model_permission('ModifierRule', 'add')(modifier_create), name='modifier_create'),
#     path('modifier/edit/<int:pk>/', check_model_permission('ModifierRule', 'edit')(modifier_edit), name='modifier_edit'),
#     path('modifier/delete/<int:pk>/', check_model_permission('ModifierRule', 'delete')(modifier_delete), name='modifier_delete'),
#
#     # ✅ Client
#     path('client/create/', check_model_permission('Client', 'add')(client_create), name='client_create'),
#     path('client/edit/<int:pk>/', check_model_permission('Client', 'edit')(client_edit), name='client_edit'),
#     path('client/delete/<int:pk>/', check_model_permission('Client', 'delete')(client_delete), name='client_delete'),
# ]



from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', login_page, name='login_page'),
    path('logout/', LogoutView.as_view(next_page='login_page'), name='logout'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/protected/', protected_view, name='protected_view'),
    path('dashboard/', unified_dashboard, name='dashboard'),
    path('export/', export_csv, name='export_csv'),

    # path('add-edit/', add_edit_insurance, name='add_edit_insurance'),
    path('import/excel/', unified_excel_import_view, name='excel_import'),

    # path('table/<str:model>/', dynamic_table_view, name='table_view'),
    path('permissions/', manage_permissions, name='manage_permissions'),
    path('model-tables/', model_tables_view, name='model_tables'),

    path('insurance/create/', insurance_create, name='insurance_create'),
    path('insurance/edit/<int:pk>/', insurance_edit, name='insurance_edit'),
    path('insurance/delete/<int:pk>/', insurance_delete, name='insurance_delete'),

    path('modifier/create/', modifier_create, name='modifier_create'),
    path('modifier/edit/<int:pk>/', modifier_edit, name='modifier_edit'),
    path('modifier/delete/<int:pk>/', modifier_delete, name='modifier_delete'),

    path('client/create/', client_create, name='client_create'),
    path('client/edit/<int:pk>/', client_edit,   name='client_edit'),
    path('client/delete/<int:pk>/', client_delete, name='client_delete'),

    path('dxcategory/create/', dxcategory_create, name='dxcategory_create'),
    path('dxcategory/edit/<int:id>/', dxcategory_edit, name='dxcategory_edit'),
    path('dxcategory/delete/<int:id>/', dxcategory_delete, name='dxcategory_delete'),

    path('scenario/create/', scenario_create, name='scenario_create'),
    path('scenario/edit/<int:pk>/', scenario_edit, name='scenario_edit'),
    path('scenario/delete/<int:pk>/', scenario_delete, name='scenario_delete'),

    path('user/create/', user_create, name='user_create'),
    path('user/edit/<int:pk>/', user_edit, name='user_edit'),
    path('user/delete/<int:pk>/', user_delete, name='user_delete'),

    path('insurance/upload/', insurance_preview_upload, name='insurance_preview_upload'),
    path('insurance/confirm-import/', insurance_confirm_import, name='insurance_confirm_import'),
    path('insurance/download/excel/', insurance_download_excel, name='insurance_download_excel'),
    # path('insurance/download/pdf/', insurance_download_pdf, name='insurance_download_pdf'),

    path('client/upload/', client_preview_upload, name='client_preview_upload'),
    path('client/confirm-import/', client_confirm_import, name='client_confirm_import'),

    path('modifier/upload/', modifier_preview_upload, name='modifier_preview_upload'),
    path('modifier/confirm-import/', modifier_confirm_import, name='modifier_confirm_import'),
    path('modifier/download/excel/', download_modifier_excel, name='download_modifier_excel'),
    # path('modifier/download/pdf/', download_modifier_pdf, name='download_modifier_pdf'),
]
