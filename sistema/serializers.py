from rest_framework import serializers

from sistema.models import DiasSemana


class GerarTreinoSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField(min_value=1)

    objetivo = serializers.CharField(
        min_length=2,
        max_length=100,
    )

    experiencia = serializers.ChoiceField(
        choices=[
            "iniciante",
            "intermediario",
            "avancado",
        ]
    )

    frequencia_semanal = serializers.IntegerField(
        min_value=1,
        max_value=7,
    )

    duracao_minutos = serializers.IntegerField(
        min_value=15,
        max_value=180,
    )

    equipamentos = serializers.ListField(
        child=serializers.CharField(
            min_length=1,
            max_length=100,
        ),
        allow_empty=False,
    )

    dias_disponiveis = serializers.ListField(
        child=serializers.ChoiceField(
            choices=DiasSemana.choices,
        ),
        allow_empty=False,
        min_length=1,
        max_length=7,
    )

    def validate(self, dados):
        dias = dados["dias_disponiveis"]

        if len(dias) != len(set(dias)):
            raise serializers.ValidationError(
                {
                    "dias_disponiveis": (
                        "Os dias disponíveis não podem se repetir."
                    )
                }
            )

        if dados["frequencia_semanal"] != len(dias):
            raise serializers.ValidationError(
                {
                    "frequencia_semanal": (
                        "A frequência deve ser igual à quantidade "
                        "de dias disponíveis."
                    )
                }
            )

        return dados