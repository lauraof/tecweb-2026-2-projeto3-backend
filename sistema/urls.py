from django.urls import path

from sistema import views

urlpatterns = [
    path("treinos/gerar/", views.gerar_treino_endpoint, name="gerar-treino",),
    path("habitos/<int:habito_id>/", views.habito_detalhe_endpoint, name="habito-detalhe",),
    path("habitos/", views.habitos_endpoint, name="habito"),
]