from django.urls import path
from . import views

urlpatterns = [
    path('', views.WorkOrderListView.as_view(), name='workorder_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.workorder_create, name='workorder_create'),
    path('<int:pk>/', views.WorkOrderDetailView.as_view(), name='workorder_detail'),
    path('<int:pk>/edit/', views.workorder_update, name='workorder_update'),
    path('<int:pk>/delete/', views.workorder_delete, name='workorder_delete'),
    path('<int:pk>/sign/', views.sign_workorder, name='sign_workorder'),
    path('<int:pk>/close/', views.close_workorder, name='close_workorder'),
    path('<int:pk>/print/', views.print_workorder, name='print_workorder'),
]