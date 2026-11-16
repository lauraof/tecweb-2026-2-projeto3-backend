from django.db import transaction

from sistema.models import Exercicio, Treino, Usuario
from sistema.schemas import PlanoTreinoSchema


@transaction.atomic
def salvar_plano_treino(
    usuario: Usuario,
    plano: PlanoTreinoSchema,
) -> Treino:
    dias_semana = [treino_do_dia.dia for treino_do_dia in plano.treinos]

    treino, _ = Treino.objects.update_or_create(
        usuario=usuario,
        defaults={
            "dias_semana": dias_semana,
        },
    )

    treino.exercicios.all().delete()

    exercicios_para_criar = []

    for treino_do_dia in plano.treinos:
        for ordem, exercicio in enumerate(
            treino_do_dia.exercicios,
            start=1,
        ):
            exercicios_para_criar.append(
                Exercicio(
                    treino=treino,
                    dia=treino_do_dia.dia,
                    nome=exercicio.nome,
                    descricao=exercicio.observacoes or "",
                    series=exercicio.series,
                    repeticoes=exercicio.repeticoes,
                    descanso=exercicio.descanso_segundos,
                    ordem=ordem,
                )
            )

    Exercicio.objects.bulk_create(exercicios_para_criar)

    return treino