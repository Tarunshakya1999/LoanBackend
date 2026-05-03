from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from myapp.views import MyTokenObtainPairView, RegisterView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth endpoints
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', RegisterView.as_view(), name='register'),

    # App endpoints
    path('api/', include('myapp.urls')),
]