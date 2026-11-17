from django.shortcuts import get_object_or_404
from google.genai import errors
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from sistema.models import Habito, Usuario
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