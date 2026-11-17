from rest_framework import serializers

from sistema.models import *


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

class HabitoSerializer(serializers.ModelSerializer):
    dias_semana = serializers.ListField(child=serializers.ChoiceField(choices=DiasSemana.choices), allow_empty=False, max_length=7)

    class Meta:
        model = Habito
        fields = ["id", "nome", "descricao", "dias_semana", "ativo", "criado_em"]
        read_only_fields = ["id"]

    def validate_dias_semana(self, dias):
        if len(dias) != len(set(dias)):
            raise serializers.ValidationError("Há dias repetidos na lista.")
        ordem = [codigo for codigo, _ in DiasSemana.choices]
        dias = sorted(dias, key=ordem.index)
        return dias

    def validate_nome(self, nome):
        nome = nome.strip()
        if not nome:
            raise serializers.ValidationError("O nome do hábito está vazio.")
        return nome