from django.urls import path

from sistema import views
from sistema import views_grupos
from sistema import views_auth

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("treinos/gerar/", views.gerar_treino_endpoint, name="gerar-treino",),
    path("habitos/<int:habito_id>/", views.habito_detalhe_endpoint, name="habito-detalhe",),
    path("habitos/", views.habitos_endpoint, name="habito"),
    path("missoes/hoje", views.missoes_diarias_endpoint, name="missoes-diarias"),
    path("dieta/metas/", views.dieta_metas_endpoint, name="dieta-metas"),
    path("dieta/hoje/", views.dieta_hoje_endpoint, name="dieta-hoje"),
    path("dieta/refeicoes/", views.concluir_refeicao_endpoint, name="concluir-refeicao"),
    path("dieta/refeicoes/<int:conclusao_id>/", views.desmarcar_refeicao_endpoint, name="desmarcar-refeicao"),
    path("habitos/", views.habitos_endpoint, name="habitos"),
    path("grupos/", views_grupos.grupos_endpoint, name="grupos"),
    path("grupos/<int:grupo_id>/", views_grupos.grupo_detalhe_endpoint, name="grupo-detalhe"),
    path("grupos/<int:grupo_id>/membros/", views_grupos.adicionar_membro_endpoint, name="grupo-adicionar-membro"),
    path("grupos/<int:grupo_id>/membros/<int:usuario_id>/", views_grupos.remover_membro_endpoint, name="grupo-remover-membro"),
    path("grupos/<int:grupo_id>/leaderboard/", views_grupos.leaderboard_grupo_endpoint, name="grupo-leaderboard"),
    path("grupos/<int:grupo_id>/participacao/", views_grupos.sair_grupo_endpoint, name="grupo-sair"),
    path("habitos/<int:habito_id>/concluir/", views.concluir_habito_endpoint, name="concluir-habito"),
    path("exercicios/<int:exercicio_id>/concluir/", views.concluir_exercicio_endpoint, name="concluir-exercicio"),
    path("auth/cadastro/", views_auth.cadastro_endpoint, name="auth-cadastro"),
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", views_auth.me_endpoint, name="auth-me"),
]