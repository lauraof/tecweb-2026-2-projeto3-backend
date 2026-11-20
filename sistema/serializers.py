from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password as validar_senha
from sistema.models import *
from django.core.exceptions import ValidationError

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


class DietaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dieta
        fields = [
            "id",
            "meta_calorias",
            "pct_carboidrato",
            "pct_proteina",
            "pct_gordura",
            "pct_cafe",
            "pct_almoco",
            "pct_lanche",
            "pct_jantar",
        ]
        read_only_fields = ["id"]

    def validate_meta_calorias(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "A meta de calorias deve ser maior que zero."
            )
        return value

    def validate(self, dados):
        # Combina os valores enviados com os já existentes.
        # Isso também permite validar atualizações parciais.
        valores = {}

        campos = [
            "pct_carboidrato",
            "pct_proteina",
            "pct_gordura",
            "pct_cafe",
            "pct_almoco",
            "pct_lanche",
            "pct_jantar",
        ]

        for campo in campos:
            if campo in dados:
                valores[campo] = dados[campo]
            elif self.instance is not None:
                valores[campo] = getattr(self.instance, campo)

        # Verifica a soma dos macronutrientes
        macros = [
            "pct_carboidrato",
            "pct_proteina",
            "pct_gordura",
        ]

        if all(campo in valores for campo in macros):
            soma_macros = sum(valores[campo] for campo in macros)

            if soma_macros != 100:
                raise serializers.ValidationError({
                    "macronutrientes":
                        "As porcentagens dos macronutrientes devem somar 100%."
                })

        # Verifica a distribuição entre refeições
        refeicoes = [
            "pct_cafe",
            "pct_almoco",
            "pct_lanche",
            "pct_jantar",
        ]

        if all(campo in valores for campo in refeicoes):
            soma_refeicoes = sum(valores[campo] for campo in refeicoes)

            if soma_refeicoes != 100:
                raise serializers.ValidationError({
                    "refeicoes":
                        "As porcentagens das refeições devem somar 100%."
                })

        return dados


class GrupoSerializer(serializers.ModelSerializer):
    objetivos = serializers.ListField(
        child=serializers.ChoiceField(
            choices=ObjetivosGrupo.choices
        ),
        allow_empty=False
    )

    class Meta:
        model = Grupo
        fields = [
            "id",
            "nome",
            "objetivos",
            "duracao_dias",
            "criado_em",
        ]
        read_only_fields = ["id", "criado_em"]

    def validate_nome(self, nome):
        nome = nome.strip()

        if not nome:
            raise serializers.ValidationError(
                "O nome do grupo não pode estar vazio."
            )

        return nome

    def validate_objetivos(self, objetivos):
        if len(objetivos) != len(set(objetivos)):
            raise serializers.ValidationError(
                "Os objetivos não podem se repetir."
            )

        return objetivos

    def create(self, validated_data):
        objetivos = validated_data.pop("objetivos")

        grupo = Grupo.objects.create(
            objetivos=",".join(objetivos),
            **validated_data
        )

        return grupo

    def to_representation(self, instance):
        dados = super().to_representation(instance)

        dados["objetivos"] = list(instance.objetivos)

        return dados


class AdicionarMembroSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField(min_value=1)


class CadastroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'email', 'password']
    
    def validate_email(self, value):
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Já existe uma conta com esse e-mail.")
        return value

    def validate_password(self, value):
        try:
            validar_senha(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value 

    def create(self, validated_data):
        return Usuario.objects.create_user(**validated_data)
    