from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from sistema.models import *


@transaction.atomic
def registrar_conclusao(
    *,
    usuario,
    tipo,
    data=None,
    exercicio=None,
    habito=None,
    refeicao=None,
):
    data = data or timezone.localdate()

    alvos = [exercicio, habito, refeicao]

    if sum(alvo is not None for alvo in alvos) != 1:
        raise ValidationError(
            "Informe exatamente um exercício, hábito ou refeição."
        )

    if tipo not in XP_POR_ACAO:
        raise ValidationError("Tipo de conclusão inválido.")

    if tipo == Acoes.EXERCICIO and exercicio is None:
        raise ValidationError("Informe o exercício concluído.")

    if tipo == Acoes.HABITO and habito is None:
        raise ValidationError("Informe o hábito concluído.")

    if tipo == Acoes.REFEICAO and refeicao is None:
        raise ValidationError("Informe a refeição concluída.")

    codigo_dia = DiasSemana.values[data.weekday()]

    if exercicio is not None:
        if exercicio.treino.usuario_id != usuario.id:
            raise ValidationError(
                "Este exercício pertence a outro usuário."
            )

        if exercicio.dia != codigo_dia:
            raise ValidationError(
                "Este exercício não está previsto para esta data."
            )

    if habito is not None:
        if habito.usuario_id != usuario.id:
            raise ValidationError(
                "Este hábito pertence a outro usuário."
            )

        if not habito.ativo:
            raise ValidationError("Este hábito está inativo.")

        if codigo_dia not in habito.dias_semana:
            raise ValidationError(
                "Este hábito não está previsto para esta data."
            )

    if refeicao is not None:
        codigos_validos = set(Refeicoes.values)

        if refeicao not in codigos_validos:
            raise ValidationError("Refeição inválida.")

        if not Dieta.objects.filter(usuario=usuario).exists():
            raise ValidationError(
                "O usuário ainda não configurou suas metas alimentares."
            )

    usuario_bloqueado = Usuario.objects.select_for_update().get(
        pk=usuario.pk
    )

    campos_alvo = {
        "exercicio": exercicio,
        "habito": habito,
        "refeicao": refeicao,
    }

    conclusao, criada = Conclusao.objects.get_or_create(
        usuario=usuario_bloqueado,
        tipo=tipo,
        data=data,
        **campos_alvo,
    )

    xp_ganho = 0

    if criada:
        xp_ganho = XP_POR_ACAO[tipo]

        MovXP.objects.create(
            usuario=usuario_bloqueado,
            quantidade=xp_ganho,
            acao=tipo,
            conclusao=conclusao,
        )

        Usuario.objects.filter(pk=usuario_bloqueado.pk).update(
            xp=F("xp") + xp_ganho
        )

        usuario_bloqueado.refresh_from_db(fields=["xp"])

    return {
        "conclusao": conclusao,
        "criada": criada,
        "xp_ganho": xp_ganho,
        "xp_total": usuario_bloqueado.xp,
        "nivel": usuario_bloqueado.nivel,
    }