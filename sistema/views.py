from django.shortcuts import get_object_or_404
from django.utils import timezone
from google.genai import errors
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from sistema.models import Habito, Usuario, DiasSemana, Conclusao, Acoes, Refeicoes, XP_POR_ACAO, GEM_POR_ACAO
from sistema.serializers import HabitoSerializer, GerarTreinoSerializer
from sistema.services.gemini import gerar_treino
from sistema.services.treinos import salvar_plano_treino

def usuario_atual(request):
    return Usuario.objects.get(id=request.headers.get("X-Usuario-Id"))

DISCLAIMER = (
    "Este treino foi gerado por inteligência artificial e possui "
    "caráter informativo. Consulte um profissional de educação física "
    "ou de saúde antes de iniciar ou modificar sua rotina de exercícios."
)


@api_view(["POST"])
def gerar_treino_endpoint(request):
    serializer = GerarTreinoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    dados = serializer.validated_data.copy()
    usuario_id = dados.pop("usuario_id")

    usuario = get_object_or_404(
        Usuario,
        id=usuario_id,
    )

    try:
        plano = gerar_treino(dados)
    except errors.APIError:
        return Response(
            {
                "erro": (
                    "O serviço de geração de treino está "
                    "temporariamente indisponível."
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except (PydanticValidationError, ValueError):
        return Response(
            {
                "erro": (
                    "O Gemini retornou um plano de treino inválido."
                )
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    treino_salvo = salvar_plano_treino(
        usuario=usuario,
        plano=plano,
    )

    resposta = plano.model_dump()
    resposta["treino_id"] = treino_salvo.id
    resposta["disclaimer"] = DISCLAIMER

    return Response(
        resposta,
        status=status.HTTP_201_CREATED,
    )

@api_view(['GET', 'PATCH', 'DELETE'])
def habito_detalhe_endpoint(request, habito_id):
    usuario = usuario_atual(request)
    habito = get_object_or_404(Habito, id=habito_id, usuario=usuario)

    if request.method == 'GET':
        serializer = HabitoSerializer(habito)
        return Response(serializer.data)

    if request.method == 'DELETE':
        habito.ativo = False
        habito.save()
        serializer = HabitoSerializer(habito)
        return Response(serializer.data)

    if request.method == 'PATCH':
        serializer = HabitoSerializer(habito, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

@api_view(['GET', 'POST'])
def habitos_endpoint(request):
    usuario = usuario_atual(request)

    if request.method == 'GET':
        habitos = Habito.objects.filter(usuario=usuario)
        serializer = HabitoSerializer(habitos, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = HabitoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(usuario=usuario)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(["GET"])
def missoes_diarias_endpoint(request):
    usuario = usuario_atual(request)
    data = timezone.localdate()
    codigo_dia = DiasSemana.values[data.weekday()]
    conclusoes = Conclusao.objects.filter(usuario=usuario, data=data)

    exercicios_feitos = set()
    habitos_feitos = set()
    refeicoes_feitas = set()

    for realizados in conclusoes:
        if realizados.tipo == Acoes.EXERCICIO:
            exercicios_feitos.add(realizados.exercicio_id)
        elif realizados.tipo == Acoes.HABITO:
            habitos_feitos.add(realizados.habito_id)
        elif realizados.tipo == Acoes.REFEICAO:
            refeicoes_feitas.add(realizados.refeicao)

    treino = getattr(usuario, "treino", None)
    bloco_treino = None

    exercicios = []
    if treino is not None:
        for exercicio in treino.exercicios.filter(dia=codigo_dia): 
            exercicios.append({"id": exercicio.id, "nome": exercicio.nome, "series": exercicio.series, "repeticoes": exercicio.repeticoes,
                    "descanso": exercicio.descanso, "concluido": exercicio.id in exercicios_feitos,
                })

        if exercicios:
            bloco_treino = {"nome": treino.nome, "total": len(exercicios), "concluidos": sum(1 for item in exercicios if item["concluido"]),
                "xp_por_item": XP_POR_ACAO[Acoes.EXERCICIO], "gemas_por_item": GEM_POR_ACAO[Acoes.EXERCICIO], "exercicios": exercicios,
            }

    habitos = []
    for habito in Habito.objects.filter(usuario=usuario, ativo=True):
        if codigo_dia in habito.dias_semana:
            habitos.append({"id": habito.id, "nome": habito.nome, "concluido": habito.id in habitos_feitos,})

    bloco_habitos = {"total": len(habitos), "concluidos": sum(1 for item in habitos if item["concluido"]), "xp_por_item": XP_POR_ACAO[Acoes.HABITO],
        "gemas_por_item": GEM_POR_ACAO[Acoes.HABITO], "itens": habitos,
    }

    dieta = getattr(usuario, "dieta", None)
    bloco_refeicoes = None

    refeicoes = []
    if dieta is not None:
        for codigo, nome in Refeicoes.choices:
            refeicoes.append({"codigo": codigo, "nome": nome, "calorias": dieta.calorias_da_refeicao(codigo), "concluida": codigo in refeicoes_feitas,
                })
        bloco_refeicoes = {
            "total": len(refeicoes),
            "concluidos": sum(1 for item in refeicoes if item["concluida"]),
            "xp_por_item": XP_POR_ACAO[Acoes.REFEICAO],
            "gemas_por_item": GEM_POR_ACAO[Acoes.REFEICAO],
            "itens": refeicoes,
        }
    return Response(
        {
            "data": data,
            "dia_semana": codigo_dia,
            "treino": bloco_treino,
            "habitos": bloco_habitos,
            "refeicoes": bloco_refeicoes,
        }
    )
