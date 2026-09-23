# -*- coding: utf-8 -*-
"""Fotos da montagem da mae da Clara que NAO entram em nenhuma versao.

A regra da v1a era nao cortar uma unica foto. Esta lista e a excecao, e cada
entrada tem de trazer o motivo escrito e a autoria de quem decidiu. Sem isso
volta a ser um corte sem dono daqui a duas semanas.

Quem decide o que entra aqui e o Tiago, nao este ficheiro.
"""

# 11/09/2026, decisao do Tiago, palavras dele:
#   "No demo 1a NAO QUERO INCLUIR OS BILHETES DOs namorados"
#
# Sao cinco fotografias de bilhetes manuscritos de admiradores da Clara, uma
# delas datada de 14/11/07. A mae da Clara construiu com eles uma piada de
# aula de portugues: "Clube de Fas", "Inspirou figuras de estilo",
# "Repeticoes e aliteracoes", "Conotacoes", "Metaforas e hiperboles".
#
# A piada e boa e e dela, mas o video passa no jantar do casamento. Cartas de
# amor de outros homens para a noiva, lidas por 140 convidados, e exatamente o
# que o filtro de tom do CLAUDE.md existe para apanhar.
#
# Os textos saem com as fotos, porque sao legendas DELAS. Sem as fotos, a piada
# nao tem sobre o que assentar. A leitura fica: "criou uma grande empatia com
# colegas e amigos" e logo a seguir a alianca de argola de porta-chaves aos 8
# anos, que continua la e e uma historia de crianca, nao de namorado.
BILHETES_DE_ADMIRADORES = [
    "8-6.jpg",      # "Es tao linda como as estrelas..."
    "8-7.jpg",      # "Es a unica rosa no meio de um campo de malmequeres", 14/11/07
    "8-8.jpg",      # "AMO-TE CLARINHA MT, MT, MT..." repetido a pagina toda
    "8-9.jpg",      # "Desculpa a caneta vermelha, aqui ela significa AMOR"
    "8-9-1.jpg",    # desenho, "Es o vermelho para o meu coracao"
]

EXCLUIDAS = set(n.lower() for n in BILHETES_DE_ADMIRADORES)


def entra(ficheiro):
    """Diz se esta foto pode entrar numa montagem."""
    return (ficheiro or "").strip().lower() not in EXCLUIDAS


def filtrar(linhas, campo="ficheiro"):
    """Tira as excluidas de uma lista de entradas, e diz quantas tirou."""
    ficam = [r for r in linhas if entra(r.get(campo))]
    return ficam, len(linhas) - len(ficam)
