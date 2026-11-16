from pydantic import BaseModel, Field


class ExercicioSchema(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    series: int = Field(ge=1, le=10)
    repeticoes: str = Field(min_length=1, max_length=30)
    descanso_segundos: int = Field(ge=0, le=600)
    observacoes: str | None = Field(default=None, max_length=300)


class TreinoDoDiaSchema(BaseModel):
    dia: str = Field(min_length=2, max_length=30)
    exercicios: list[ExercicioSchema] = Field(min_length=1)


class PlanoTreinoSchema(BaseModel):
    resumo: str = Field(min_length=2, max_length=500)
    treinos: list[TreinoDoDiaSchema] = Field(min_length=1)