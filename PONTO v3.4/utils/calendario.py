
from datetime import date, timedelta

def pascoa(ano):
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    mes = (h + l - 7*m + 114) // 31
    dia = ((h + l - 7*m + 114) % 31) + 1
    return date(ano, mes, dia)

def feriados_nacionais_para(ano):
    P = pascoa(ano)
    carnaval = P - timedelta(days=47)
    sexta_santa = P - timedelta(days=2)
    corpus_christi = P + timedelta(days=60)
    return {
        date(ano,1,1): "Confraternização Universal",
        carnaval: "Carnaval",
        sexta_santa: "Sexta-Feira Santa",
        P: "Páscoa",
        date(ano,4,21): "Tiradentes",
        date(ano,5,1): "Dia do Trabalho",
        corpus_christi: "Corpus Christi",
        date(ano,9,7): "Independência do Brasil",
        date(ano,10,12): "Nossa Senhora Aparecida",
        date(ano,11,2): "Finados",
        date(ano,11,15): "Proclamação da República",
        date(ano,12,25): "Natal"
    }
