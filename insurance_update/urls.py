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
    path('add-edit/', add_edit_insurance, name='add_edit_insurance'),
    path('import/excel/', unified_excel_import_view, name='excel_import'),

    path('table/<str:model>/', dynamic_table_view, name='table_view'),
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
]
