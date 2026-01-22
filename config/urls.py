from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

import core.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # URLs de l'application principale
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', core.views.logout_view, name='logout'),
    path('register/', core.views.register, name='register'),
   
]

