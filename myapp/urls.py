from django.urls import path
from .views import (
    DashboardView,
    ProfileView,
    CustomerListCreateView,
    CustomerDetailView,
    TransactionListCreateView,
    TransactionDeleteView,
)

urlpatterns = [
    path('dashboard/',  DashboardView.as_view(),  name='dashboard'),
    path('profile/',    ProfileView.as_view(),     name='profile'),

    path('customers/',            CustomerListCreateView.as_view(), name='customer-list-create'),
    path('customers/<int:pk>/',   CustomerDetailView.as_view(),     name='customer-detail'),

    path('customers/<int:customer_id>/transactions/', TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/<int:pk>/',                    TransactionDeleteView.as_view(),     name='transaction-delete'),
]