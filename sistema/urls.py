from django.urls import path

from sistema import views

urlpatterns = [
    path("treinos/gerar/", views.gerar_treino_endpoint, name="gerar-treino",),
    path("habitos/<int:habito_id>/", views.habito_detalhe_endpoint, name="habito-detalhe",),
    path("habitos/", views.habitos_endpoint, name="habito"),
    path("dieta/metas/", views.dieta_metas_endpoint, name="dieta-metas"),
    path("dieta/hoje/", views.dieta_hoje_endpoint, name="dieta-hoje"),
    path("dieta/refeicoes/", views.concluir_refeicao_endpoint, name="concluir-refeicao"),
    path("dieta/refeicoes/<int:conclusao_id>/", views.desmarcar_refeicao_endpoint, name="desmarcar-refeicao"),
    path("habitos/", views.habitos_endpoint, name="habitos"),
]