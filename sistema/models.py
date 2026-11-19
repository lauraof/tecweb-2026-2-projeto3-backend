from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from multiselectfield import MultiSelectField

# Regras de gamificação
XP_POR_ACAO = {
    "EXERCICIO": 2,
    "REFEICAO": 3,
    "HABITO": 4,
}
GEM_POR_ACAO = { 
    "EXERCICIO": 1, 
    "REFEICAO" : 2, 
    "HABITO" : 1,
}
XP_POR_NIVEL = 100



class DiasSemana(models.TextChoices):
    SEGUNDA = "SEG", "Segunda-feira"
    TERCA = "TER", "Terça-feira"
    QUARTA = "QUA", "Quarta-feira"
    QUINTA = "QUI", "Quinta-feira"
    SEXTA = "SEX", "Sexta-feira"
    SABADO = "SAB", "Sábado"
    DOMINGO = "DOM", "Domingo"


class Acoes(models.TextChoices):
    EXERCICIO = "EXERCICIO", "Exercício"
    REFEICAO = "REFEICAO", "Refeição"
    HABITO = "HABITO", "Hábito"


class Refeicoes(models.TextChoices):
    CAFE = "CAFE", "Café da manhã"
    ALMOCO = "ALMOCO", "Almoço"
    LANCHE = "LANCHE", "Lanche"
    JANTAR = "JANTAR", "Jantar"


class Usuario(models.Model):
    nome = models.CharField(max_length=30, unique=True)
    senha = models.CharField(max_length=255) 
    xp = models.PositiveIntegerField(default=0)
    gemas = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    ultima_atividade = models.DateField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-xp", "nome"]

    @property
    def nivel(self): 
        return self.xp // XP_POR_NIVEL + 1

    @property
    def xp_no_nivel(self):
        return self.xp % XP_POR_NIVEL

    def set_senha(self, senha_crua):
        from django.contrib.auth.hashers import make_password
        self.senha = make_password(senha_crua)

    def checar_senha(self, senha_crua):
        from django.contrib.auth.hashers import check_password
        return check_password(senha_crua, self.senha)

    def __str__(self):
        return self.nome


class Treino(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="treino")
    nome = models.CharField(max_length=100, default="Meu treino")
    dias_semana = MultiSelectField(choices=DiasSemana.choices, max_length=27)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.usuario.nome})"


class Exercicio(models.Model):
    treino = models.ForeignKey(Treino, on_delete=models.CASCADE, related_name="exercicios")
    dia = models.CharField(max_length=3, choices=DiasSemana.choices)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    series = models.PositiveSmallIntegerField(default=3)
    repeticoes = models.CharField(max_length=20)   
    carga_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    descanso = models.PositiveIntegerField(help_text="Descanso em segundos")
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["dia", "ordem"]

    def __str__(self):
        return f"{self.nome} - {self.get_dia_display()}"


class Dieta(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, related_name="dieta"
    )
    meta_calorias = models.PositiveIntegerField()

    pct_carboidrato = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    pct_proteina = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    pct_gordura = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])

    pct_cafe = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    pct_almoco = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    pct_lanche = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    pct_jantar = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])

    def clean(self):
        macros = self.pct_carboidrato + self.pct_proteina + self.pct_gordura
        if macros != 100:
            raise ValidationError(f"Os macros devem somar 100%. Agora somam {macros}%).")
        
        refeicoes = self.pct_cafe + self.pct_almoco + self.pct_lanche + self.pct_jantar
        if refeicoes != 100:
            raise ValidationError(f"As refeições devem somar 100%. Agora somam {refeicoes}%).")

    def calorias_da_refeicao(self, refeicao):
        opcoes = {
            Refeicoes.CAFE: self.pct_cafe,
            Refeicoes.ALMOCO: self.pct_almoco,
            Refeicoes.LANCHE: self.pct_lanche,
            Refeicoes.JANTAR: self.pct_jantar,
        }
        return round(self.meta_calorias * opcoes[refeicao] / 100)

    def __str__(self):
        return f"Dieta de {self.usuario.nome}"


class Habito(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="habitos")
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    dias_semana = MultiSelectField(choices=DiasSemana.choices, max_length=27)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Conclusao(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="conclusoes")
    tipo = models.CharField(max_length=10, choices=Acoes.choices)
    data = models.DateField()

    exercicio = models.ForeignKey(Exercicio, on_delete=models.CASCADE, null=True, blank=True)
    habito = models.ForeignKey(Habito, on_delete=models.CASCADE, null=True, blank=True)
    refeicao = models.CharField(max_length=10, choices=Refeicoes.choices, null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "data", "exercicio"],
                condition=models.Q(exercicio__isnull=False),
                name="unico_exercicio_por_dia",
            ),
            models.UniqueConstraint(
                fields=["usuario", "data", "habito"],
                condition=models.Q(habito__isnull=False),
                name="unico_habito_por_dia",
            ),
            models.UniqueConstraint(
                fields=["usuario", "data", "refeicao"],
                condition=models.Q(refeicao__isnull=False),
                name="unica_refeicao_por_dia",
            ),
        ]

    def clean(self):
        alvos = [self.exercicio, self.habito, self.refeicao]
        if sum(1 for a in alvos if a is not None) != 1:
            raise ValidationError("Informe exatamente um entre exercicio, habito ou refeicao.")

    def __str__(self):
        return f"{self.usuario.nome} - {self.tipo} em {self.data}"


class MovXP(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="movimentacoes_xp")
    quantidade = models.IntegerField()
    acao = models.CharField(max_length=10, choices=Acoes.choices)
    conclusao = models.ForeignKey(Conclusao, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["conclusao"],
                condition=models.Q(conclusao__isnull=False),
                name="mov_xp_unica_por_conclusao",
            ),
        ]

    def __str__(self):
        sinal = "+" if self.quantidade >= 0 else ""
        return f"{self.usuario.nome}: {sinal}{self.quantidade} XP ({self.acao})"


    
class ObjetivosGrupo(models.TextChoices):
    TREINO = "EXERCICIO", "Treino"
    REFEICOES = "REFEICAO", "Refeições"
    HABITOS = "HABITO", "Hábitos"


class Grupo(models.Model):
    nome = models.CharField(max_length=100)

    criador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="grupos_criados"
    )

    objetivos = MultiSelectField(
        choices=ObjetivosGrupo.choices,
        max_length=30
    )

    duracao_dias = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(365)
        ],
        default=30
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    membros = models.ManyToManyField(
        Usuario,
        through="ParticipacaoGrupo",
        related_name="grupos"
    )

    def __str__(self):
        return self.nome


class ParticipacaoGrupo(models.Model):
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name="participacoes"
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="participacoes_grupos"
    )

    entrou_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["grupo", "usuario"],
                name="participacao_unica_por_grupo"
            )
        ]

    def __str__(self):
        return f"{self.usuario.nome} - {self.grupo.nome}"
