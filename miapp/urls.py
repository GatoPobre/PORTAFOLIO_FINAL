from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import FormularioLoginPersonalizado
from . import views
from .views import (
    register,
    DashboardMixinView,
)


app_name = 'miapp'

urlpatterns = [

    path('', views.inicio, name="inicio"),
    path('contacto/', views.contacto, name="contacto"),
    path('politicas-de-privacidad/', views.politicas_privacidad, name="politicas"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html",
         form_class=FormularioLoginPersonalizado), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("register/", register, name="registro"),


    path("dashboard/", DashboardMixinView.as_view(), name="dashboard"),
    path("actualizar_perfil/", views.actualizar_perfil, name="actualizar_perfil"),
    path('cambiar_password/',
         views.cambiar_password, name='cambiar_password'),
]
