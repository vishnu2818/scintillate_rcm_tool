from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('login/', login_page, name='login_page'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/protected/', protected_view, name='protected_view'),
    path('dashboard/', unified_dashboard, name='dashboard'),
    path('export/', export_csv, name='export_csv'),
    path('add-edit/', add_edit_insurance, name='add_edit_insurance'),
    path('import/excel/', unified_excel_import_view, name='excel_import'),
]
