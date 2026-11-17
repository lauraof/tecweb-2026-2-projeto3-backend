from django.urls import path

from sistema import views


urlpatterns = [
    path("treinos/gerar/", views.gerar_treino_endpoint,name="gerar-treino",),
    path()
]