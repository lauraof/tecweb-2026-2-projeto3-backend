
from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from sistema.models import (
    Usuario,
    Grupo,
    ParticipacaoGrupo,
    MovXP,
)

from sistema.serializers import (
    GrupoSerializer,
    AdicionarMembroSerializer,
)


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def usuario_atual(request):
    usuario_id = request.headers.get("X-Usuario-Id")
    return get_object_or_404(Usuario, id=usuario_id)


def grupo_do_usuario(grupo_id, usuario):
    return get_object_or_404(
        Grupo,
        id=grupo_id,
        membros=usuario
    )


def dados_grupo(grupo):
    dados = GrupoSerializer(grupo).data

    dados["criador"] = {
        "id": grupo.criador.id,
        "nome": grupo.criador.nome,
    }

    dados["total_membros"] = grupo.participacoes.count()

    return dados


# ==========================================
# LISTAR E CRIAR GRUPOS
# ==========================================

@api_view(["GET", "POST"])
def grupos_endpoint(request):
    usuario = usuario_atual(request)

    if request.method == "GET":
        grupos = Grupo.objects.filter(
            membros=usuario
        ).distinct().order_by("-criado_em")

        return Response([
            dados_grupo(grupo)
            for grupo in grupos
        ])

    serializer = GrupoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():
        grupo = serializer.save(criador=usuario)

        ParticipacaoGrupo.objects.create(
            grupo=grupo,
            usuario=usuario
        )

    return Response(
        dados_grupo(grupo),
        status=status.HTTP_201_CREATED
    )


# ==========================================
# DETALHES DE UM GRUPO
# ==========================================

@api_view(["GET"])
def grupo_detalhe_endpoint(request, grupo_id):
    usuario = usuario_atual(request)
    grupo = grupo_do_usuario(grupo_id, usuario)

    dados = dados_grupo(grupo)

    dados["membros"] = [
        {
            "id": participacao.usuario.id,
            "nome": participacao.usuario.nome,
            "entrou_em": participacao.entrou_em,
        }
        for participacao in grupo.participacoes.select_related(
            "usuario"
        )
    ]

    return Response(dados)


# ==========================================
# ADICIONAR MEMBROS
# ==========================================

@api_view(["POST"])
def adicionar_membro_endpoint(request, grupo_id):
    usuario = usuario_atual(request)
    grupo = grupo_do_usuario(grupo_id, usuario)

    if grupo.criador_id != usuario.id:
        return Response(
            {"erro": "Apenas o criador pode adicionar membros."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = AdicionarMembroSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    novo_usuario = get_object_or_404(
        Usuario,
        id=serializer.validated_data["usuario_id"]
    )

    participacao, criada = ParticipacaoGrupo.objects.get_or_create(
        grupo=grupo,
        usuario=novo_usuario
    )

    return Response(
        {
            "usuario_id": novo_usuario.id,
            "nome": novo_usuario.nome,
            "adicionado": criada
        },
        status=(
            status.HTTP_201_CREATED
            if criada
            else status.HTTP_200_OK
        )
    )


# ==========================================
# REMOVER MEMBRO
# ==========================================

@api_view(["DELETE"])
def remover_membro_endpoint(request, grupo_id, usuario_id):
    usuario = usuario_atual(request)
    grupo = grupo_do_usuario(grupo_id, usuario)

    if grupo.criador_id != usuario.id:
        return Response(
            {"erro": "Apenas o criador pode remover membros."},
            status=status.HTTP_403_FORBIDDEN
        )

    if usuario_id == grupo.criador_id:
        return Response(
            {"erro": "O criador não pode ser removido do grupo."},
            status=status.HTTP_400_BAD_REQUEST
        )

    participacao = get_object_or_404(
        ParticipacaoGrupo,
        grupo=grupo,
        usuario_id=usuario_id
    )

    participacao.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================
# SAIR DO GRUPO
# ==========================================

@api_view(["DELETE"])
def sair_grupo_endpoint(request, grupo_id):
    usuario = usuario_atual(request)
    grupo = grupo_do_usuario(grupo_id, usuario)

    if grupo.criador_id == usuario.id:
        return Response(
            {
                "erro": (
                    "O criador não pode sair do grupo. "
                    "Remova os demais membros antes de excluir "
                    "ou transferir a administração."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    ParticipacaoGrupo.objects.filter(
        grupo=grupo,
        usuario=usuario
    ).delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================
# LEADERBOARD POR OBJETIVO
# ==========================================

@api_view(["GET"])
def leaderboard_grupo_endpoint(request, grupo_id):
    usuario = usuario_atual(request)
    grupo = grupo_do_usuario(grupo_id, usuario)

    agora = timezone.now()

    inicio_grupo = grupo.criado_em
    fim_grupo = inicio_grupo + timedelta(
        days=grupo.duracao_dias
    )

    fim_consulta = min(agora, fim_grupo)

    objetivos = list(grupo.objetivos)

    ranking = []

    participacoes = grupo.participacoes.select_related(
        "usuario"
    )

    for participacao in participacoes:
        inicio_participante = max(
            inicio_grupo,
            participacao.entrou_em
        )

        pontos = 0

        if inicio_participante < fim_consulta:
            pontos = (
                MovXP.objects.filter(
                    usuario=participacao.usuario,
                    acao__in=objetivos,
                    criado_em__gte=inicio_participante,
                    criado_em__lte=fim_consulta
                ).aggregate(
                    total=Sum("quantidade")
                )["total"] or 0
            )

        ranking.append({
            "usuario_id": participacao.usuario.id,
            "nome": participacao.usuario.nome,
            "xp": pontos
        })

    ranking.sort(
        key=lambda item: (-item["xp"], item["nome"])
    )

    for posicao, participante in enumerate(ranking, start=1):
        participante["posicao"] = posicao

    return Response({
        "grupo_id": grupo.id,
        "nome": grupo.nome,
        "objetivos": objetivos,
        "inicio": inicio_grupo,
        "fim": fim_grupo,
        "encerrado": agora >= fim_grupo,
        "ranking": ranking
    })
