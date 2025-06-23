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
]
