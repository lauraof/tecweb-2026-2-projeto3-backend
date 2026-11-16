import json

from django.conf import settings
from google import genai

from sistema.schemas import PlanoTreinoSchema


def montar_prompt(questionario: dict) -> str:
    dados_questionario = json.dumps(
        questionario,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
Crie um plano de treino usando exclusivamente os dados deste questionário:

{dados_questionario}

Regras:
- Crie exatamente um treino para cada dia disponível.
- Cada treino deve ser identificado somente pelo campo "dia".
- O campo "dia" deve usar exatamente um destes códigos:
  SEG, TER, QUA, QUI, SEX, SAB ou DOM.
- SEG representa segunda-feira.
- TER representa terça-feira.
- QUA representa quarta-feira.
- QUI representa quinta-feira.
- SEX representa sexta-feira.
- SAB representa sábado.
- DOM representa domingo.
- Não crie nomes como "Treino A", "Treino B" ou semelhantes.
"""


def gerar_treino(questionario: dict) -> PlanoTreinoSchema:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não foi configurada.")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=montar_prompt(questionario),
        config={
            "response_mime_type": "application/json",
            "response_schema": PlanoTreinoSchema,
        },
    )

    if isinstance(response.parsed, PlanoTreinoSchema):
        plano = response.parsed
    else:
        plano = PlanoTreinoSchema.model_validate_json(response.text)

    dias_esperados = set(questionario.get("dias_disponiveis", []))
    dias_retornados = {treino.dia for treino in plano.treinos}

    if (
        dias_retornados != dias_esperados
        or len(plano.treinos) != len(dias_esperados)
    ):
        raise ValueError(
            "O Gemini não retornou exatamente um treino para cada dia disponível."
        )

    return plano