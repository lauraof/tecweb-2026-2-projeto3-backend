from django.contrib import admin
from .models import *

admin.site.register([Usuario, Treino, Exercicio, Dieta, Habito, Conclusao, MovXP])
