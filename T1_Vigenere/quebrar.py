"""
quebrar.py  -  PARTE 2 DO ENUNCIADO: CRIPTOANÁLISE DA CIFRA DE VIGENÈRE

Recupera o texto original a partir do texto cifrado SEM conhecer a senha,
assumindo que o idioma do texto é português.

Uso:
    python3 quebrar.py <texto_criptografado.txt> [arquivo_de_saida.txt] [tamanho_maximo_da_senha]

    - O arquivo de saída padrão é texto_decifrado.txt.
    - Por padrão são testados tamanhos de senha de 1 até 20.

Fluxo (na mesma ordem do enunciado):
    Etapa 1 - Descoberta do tamanho da senha ..... Índice de Coincidência (IC)
    Etapa 2 - Análise de frequência .............. uma letra da senha por posição
    Saída   - tamanho estimado, senha recuperada e texto_decifrado.txt

A ideia central do ataque: se a senha tem tamanho T, então as letras nas
posições 0, T, 2T, ... foram todas deslocadas pela MESMA letra da senha
(uma Cifra de César simples). Descobrindo T, o problema vira "quebrar T
cifras de César", o que se faz com estatística de frequência de letras.
"""

import os
import sys
import time

from higienizacao import (ALFABETO, ler_arquivo, salvar_arquivo, higienizar_texto,
                          letra_para_numero, numero_para_letra)

# Tamanhos de senha testados por padrão: 1, 2, ..., 20 (o 3º argumento da linha
# de comando muda isso). Não vale a pena exagerar no máximo: quanto maior o
# tamanho testado, menores ficam os subtextos e mais "ruidoso" fica o IC deles,
# o que atrapalha em textos curtos. Medido em 40 trechos consecutivos de 500
# letras do livro (a partir da letra 500) com a senha "segredo": testando até
# 20 o tamanho sai certo em 38 de 40 trechos; testando até 30, em 31 de 40.
# No livro inteiro não faz diferença.
TAMANHO_MAXIMO_PADRAO = 20


# ============================================================================
# FERRAMENTA BÁSICA: contar quantas vezes cada letra aparece
# ============================================================================

def contar_letras(texto):
    """
    Devolve uma lista de 26 posições: contagem[0] = quantos 'a' existem,
    contagem[1] = quantos 'b', ..., contagem[25] = quantos 'z'.

    São 26 chamadas a texto.count(letra). Cada uma percorre o texto inteiro,
    mas str.count é implementado em C e por isso é várias vezes mais rápido
    do que um laço em Python letra por letra (isso importa: o ataque conta
    letras centenas de vezes em um texto de centenas de milhares de letras;
    só a Etapa 1, com máximo 20, conta 1 + 2 + ... + 20 = 210 subtextos).
    """
    contagem = []
    for letra in ALFABETO:
        contagem.append(texto.count(letra))
    return contagem


# ============================================================================
# ETAPA 1 - DESCOBERTA DO TAMANHO DA SENHA (ÍNDICE DE COINCIDÊNCIA)
# ============================================================================
#
# Índice de Coincidência (IC) = probabilidade de duas letras sorteadas ao
# acaso no texto serem iguais.
#
#   - Texto em português: IC ~ 0,077  (letras como a, e, o são muito comuns,
#     então é fácil sortear duas iguais).
#   - Texto "embaralhado" (letras aparecendo de forma quase uniforme):
#     IC ~ 1/26 ~ 0,038.
#
# A Cifra de César NÃO muda o IC (só troca os nomes das letras, as contagens
# continuam as mesmas). Já a Vigenère mistura várias Césares, e a mistura
# "achata" as frequências, derrubando o IC (com a senha "segredo" ele cai
# para ~0,047; quanto mais letras diferentes a senha tiver, mais perto de
# 0,038 ele chega).
#
# Logo: se dividirmos o texto cifrado em T subtextos (um por posição da
# senha) e T for o tamanho certo, cada subtexto é uma César pura e o IC
# médio volta a ser ~0,077. Se T estiver errado, o IC médio fica baixo.

IC_PORTUGUES = 0.077             # medido no próprio Dom Casmurro higienizado
IC_ALEATORIO = 1 / 26            # ~ 0,038
LIMIAR_PARECE_PORTUGUES = 0.06   # meio do caminho entre os dois valores acima
MARGEM_DO_MAXIMO = 0.95          # ver explicação em escolher_tamanho_senha()
MINIMO_LETRAS_POR_POSICAO = 70   # com menos, a Etapa 2 começa a errar letras (medido em trechos do livro)


def indice_de_coincidencia(texto):
    """
    IC = soma, para cada letra, de n_i * (n_i - 1)   dividido por   N * (N - 1)

    onde n_i é quantas vezes a letra i aparece e N é o total de letras.
    (n_i * (n_i - 1) conta os pares de posições que têm a mesma letra i;
     N * (N - 1) conta todos os pares possíveis de posições.)
    """
    total = len(texto)
    if total < 2:
        return 0.0

    contagem = contar_letras(texto)
    soma = 0
    for n_i in contagem:
        soma += n_i * (n_i - 1)
    return soma / (total * (total - 1))


def dividir_em_subtextos(texto, tamanho):
    """
    Separa o texto em 'tamanho' subtextos.
    O subtexto i contém as letras das posições i, i+tamanho, i+2*tamanho, ...
    ou seja, todas as letras que foram cifradas com a MESMA letra da senha.

    Exemplo com tamanho 3 e texto "abcdefg":
        subtexto 0: a d g      (posições 0, 3, 6)
        subtexto 1: b e        (posições 1, 4)
        subtexto 2: c f        (posições 2, 5)

    Em Python, texto[i::tamanho] significa "começa em i e pula de tamanho
    em tamanho".
    """
    subtextos = []
    for i in range(tamanho):
        subtextos.append(texto[i::tamanho])
    return subtextos


def ic_medio_dos_subtextos(texto, tamanho):
    """Média dos IC dos subtextos obtidos supondo senha de tamanho 'tamanho'."""
    subtextos = dividir_em_subtextos(texto, tamanho)
    soma = 0.0
    for subtexto in subtextos:
        soma += indice_de_coincidencia(subtexto)
    return soma / tamanho


def calcular_tabela_ic(texto, tamanho_maximo):
    """
    Devolve uma lista de pares (tamanho, ic_medio) para tamanho = 1..máximo.
    É a tabela que o enunciado pede para comparar.
    """
    tabela = []
    for tamanho in range(1, tamanho_maximo + 1):
        tabela.append((tamanho, ic_medio_dos_subtextos(texto, tamanho)))
    return tabela


def escolher_tamanho_senha(tabela):
    """
    Escolhe o tamanho mais provável da senha a partir da tabela de IC.

    ARMADILHA DOS MÚLTIPLOS: se a senha tem 7 letras, os tamanhos 14 e 21
    também dão IC alto, porque dividir em 14 subtextos ainda deixa cada
    subtexto com uma César pura (a senha "segredosegredo" cifra exatamente
    igual a "segredo"). Então NÃO basta pegar o maior IC da tabela: o maior
    pode cair em um múltiplo, e aí a senha recuperada sairia repetida.
    Ex.: "segredo" no Dom Casmurro -> IC(7) = IC(14) = 0,0768 e o resto
    ~0,047; a regra abaixo escolhe o 7.

    Regra usada: pega-se o maior IC da tabela e escolhe-se o MENOR tamanho
    cujo IC chega a pelo menos 95% desse máximo. Tamanhos errados ficam bem
    abaixo disso (~0,047), e os múltiplos, embora altos, perdem para o
    tamanho verdadeiro por ele ser menor.

    Por que uma fração do máximo, e não um valor fixo (ex.: 0,06)? Porque um
    DIVISOR do tamanho certo pode ter IC "meio alto". Ex.: "criptografia"
    (12 letras) com tamanho 6 forma o subtexto (r,r), que é uma César pura,
    e os outros cinco misturam só duas Césares: IC(6) = 0,0625, acima de
    0,06, mas só 82% de IC(12) = 0,0768. A fração do máximo descarta o 6.

    Por que 95% e não menos (ex.: 90%)? Senhas com letras repetidas em
    posições regulares sobem ainda mais o IC de um divisor. Ex.: "banana"
    (6 letras) com tamanho 2 forma os subtextos (b,n,n) e (a,a,a); o segundo
    é uma César pura e o primeiro quase, então IC(2) = 0,0708, ou seja, 92%
    de IC(6) = 0,0768. Com a margem em 95% o tamanho 2 é descartado e o 6 é
    escolhido; com 90% o ataque erraria.
    """
    maior_ic = 0.0
    for tamanho, ic in tabela:
        if ic > maior_ic:
            maior_ic = ic

    # A tabela está em ordem crescente de tamanho, então o primeiro que
    # passar do limite é o menor. (O laço sempre devolve algo: o tamanho que
    # tem o maior IC passa do limite com certeza.)
    for tamanho, ic in tabela:
        if ic >= MARGEM_DO_MAXIMO * maior_ic:
            return tamanho


def imprimir_tabela_ic(tabela, tamanho_escolhido):
    """Mostra a tabela de IC por tamanho (com uma barra visual) e marca o escolhido."""
    print()
    print('Etapa 1 - Índice de Coincidência (IC) por tamanho de senha')
    print(f'  (português ~ {IC_PORTUGUES:.3f} | aleatório ~ {IC_ALEATORIO:.3f})')
    print('  Tamanho   IC médio')
    for tamanho, ic in tabela:
        barra = '#' * int(ic * 500)
        marca = ''
        if tamanho == tamanho_escolhido:
            marca = '  <-- tamanho escolhido'
        print(f'  {tamanho:7d}   {ic:.4f}  {barra}{marca}')
    print()


# ============================================================================
# ETAPA 2 - ANÁLISE DE FREQUÊNCIA (UMA LETRA DA SENHA POR POSIÇÃO)
# ============================================================================
#
# Cada subtexto é uma Cifra de César com deslocamento desconhecido (a letra
# da senha naquela posição). Para descobrir o deslocamento, testamos os 26
# possíveis: para cada um, "desfazemos" o deslocamento e medimos o quanto as
# frequências resultantes se parecem com as do português. O deslocamento
# que dá o melhor encaixe é a letra da senha.
#
# A medida de encaixe usada é o produto escalar entre a frequência observada
# e a frequência esperada (uma correlação: quanto maior, mais parecido).
# A alternativa clássica é o teste do qui-quadrado,
#     qui² = soma( (observado_i - esperado_i)² / esperado_i ),
# em que o MENOR valor vence. No livro inteiro os dois dão o mesmo resultado,
# mas o qui-quadrado divide pela frequência esperada, e letras raríssimas em
# português (k, w, y ~ 0,01%) fazem essa divisão explodir em textos curtos:
# basta um 'k' no lugar errado para a parcela dele valer centenas. O produto
# escalar não tem esse problema, por isso foi o escolhido.

# Frequência típica das letras em português (em %, tabela comumente citada).
FREQUENCIA_PORTUGUES_PORCENTO = {
    'a': 14.63, 'b': 1.04, 'c': 3.88, 'd': 4.99, 'e': 12.57, 'f': 1.02,
    'g': 1.30, 'h': 1.28, 'i': 6.18, 'j': 0.40, 'k': 0.02, 'l': 2.78,
    'm': 4.74, 'n': 5.05, 'o': 10.73, 'p': 2.52, 'q': 1.20, 'r': 6.53,
    's': 7.81, 't': 4.34, 'u': 4.63, 'v': 1.67, 'w': 0.01, 'x': 0.21,
    'y': 0.01, 'z': 0.47,
}


def montar_frequencia_esperada():
    """
    Converte a tabela em % para uma lista de 26 posições (0 = 'a', 25 = 'z')
    com frequências que somam exatamente 1 (a tabela em % soma ~100,01).
    """
    soma_da_tabela = sum(FREQUENCIA_PORTUGUES_PORCENTO.values())
    frequencias = []
    for letra in ALFABETO:
        frequencias.append(FREQUENCIA_PORTUGUES_PORCENTO[letra] / soma_da_tabela)
    return frequencias


FREQUENCIA_ESPERADA = montar_frequencia_esperada()


def pontuacao_de_encaixe(contagem_observada, total_letras):
    """
    Mede o quanto as contagens observadas "encaixam" nas frequências do
    português: multiplica, letra a letra, a frequência observada pela
    frequência esperada e soma tudo (produto escalar entre os dois vetores).

        pontuacao = soma, para cada letra i, de  (observado_i / total) * esperado_i

    Se o deslocamento testado for o certo, os picos do texto (a, e, o, s)
    caem exatamente sobre os picos da tabela do português e a soma fica ALTA.
    Se for errado, os picos caem sobre letras raras e a soma fica baixa.
    Quanto MAIOR o valor, mais o texto se parece com português.
    """
    pontuacao = 0.0
    for i in range(26):
        frequencia_observada = contagem_observada[i] / total_letras
        pontuacao += frequencia_observada * FREQUENCIA_ESPERADA[i]
    return pontuacao


def descobrir_deslocamento(subtexto):
    """
    Testa os 26 deslocamentos possíveis e devolve o que deixa o subtexto
    mais parecido com português.

    Truque para não decifrar o subtexto 26 vezes: contamos as letras UMA vez.
    Se o deslocamento for d, a letra original i virou (i + d) no cifrado;
    logo, a contagem da letra original i é a contagem da letra (i + d) mod 26
    do cifrado. Basta "girar" a lista de contagens.
    Ex.: com d = 4 ('e'), a quantidade de 'a' originais é a quantidade de 'e'
    no cifrado, porque 'a' + 'e' = 0 + 4 = 4 -> 'e'.
    """
    contagem_cifrada = contar_letras(subtexto)
    total_letras = len(subtexto)

    melhor_deslocamento = 0
    melhor_pontuacao = -1.0

    for deslocamento in range(26):
        contagem_decifrada = []
        for i in range(26):
            contagem_decifrada.append(contagem_cifrada[(i + deslocamento) % 26])

        pontuacao = pontuacao_de_encaixe(contagem_decifrada, total_letras)
        if pontuacao > melhor_pontuacao:
            melhor_pontuacao = pontuacao
            melhor_deslocamento = deslocamento

    return melhor_deslocamento


def descobrir_senha(texto_cifrado, tamanho_senha):
    """
    Divide o texto cifrado em subtextos (um por posição da senha) e
    descobre o deslocamento de cada um. O deslocamento vira a letra da senha:
    deslocamento 0 = 'a', 1 = 'b', ..., 18 = 's' etc.
    """
    subtextos = dividir_em_subtextos(texto_cifrado, tamanho_senha)
    letras_da_senha = []
    for subtexto in subtextos:
        deslocamento = descobrir_deslocamento(subtexto)
        letras_da_senha.append(numero_para_letra(deslocamento))
    return ''.join(letras_da_senha)


def imprimir_tabela_senha(texto_cifrado, senha):
    """
    Mostra, posição por posição, o raciocínio da Etapa 2: quantas letras tem
    o subtexto, qual é a letra mais comum nele (ainda cifrada), o
    deslocamento encontrado e a letra da senha correspondente.

    Detalhe bom de mostrar na apresentação: como 'a' é a letra mais comum do
    português, a letra mais comum de cada subtexto cifrado costuma ser
    exatamente 'a' + deslocamento = a própria letra da senha. (Em um texto
    em inglês a mais comum seria 'e', e a tabela tenderia a mostrar
    'e' + deslocamento.)
    """
    subtextos = dividir_em_subtextos(texto_cifrado, len(senha))
    print('Etapa 2 - Análise de frequência (uma letra da senha por posição)')
    print('  Posição   Letras   Mais comum (cifrado)   Deslocamento   Letra da senha')
    for i in range(len(senha)):
        contagem = contar_letras(subtextos[i])
        mais_comum = numero_para_letra(contagem.index(max(contagem)))
        deslocamento = letra_para_numero(senha[i])
        print(f'  {i + 1:7d}   {len(subtextos[i]):6d}   {mais_comum:^20}   {deslocamento:12d}   {senha[i]:^14}')
    print()


def aplicar_deslocamento_inverso(texto_cifrado, senha):
    """
    Reconstrói o texto original: é a Vigenère "ao contrário", subtraindo a
    letra da senha em vez de somar.

        original[i] = ( cifrado[i] - senha[i mod tamanho_da_senha] ) mod 26

    Ex.: 'g' - 'e' = 6 - 4 = 2 -> 'c'
         'b' - 'e' = 1 - 4 = -3 -> (-3) mod 26 = 23 -> 'x'

    O "mod 26" cuida dos casos em que a subtração fica negativa (em Python,
    (-3) % 26 já devolve 23, então não é preciso tratar o "dar a volta" à mão).
    """
    tamanho_senha = len(senha)
    resultado = []

    for i in range(len(texto_cifrado)):
        numero_cifrado = letra_para_numero(texto_cifrado[i])
        numero_senha = letra_para_numero(senha[i % tamanho_senha])
        numero_original = (numero_cifrado - numero_senha) % 26
        resultado.append(numero_para_letra(numero_original))

    return ''.join(resultado)


# ============================================================================
# PROGRAMA PRINCIPAL
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print('Uso: python3 quebrar.py <texto_criptografado.txt> [arquivo_de_saida.txt] [tamanho_maximo_da_senha]')
        print('Exemplo: python3 quebrar.py texto_criptografado.txt')
        sys.exit(1)
    if len(sys.argv) > 4:
        print('Erro: argumentos demais.')
        print('Uso: python3 quebrar.py <texto_criptografado.txt> [arquivo_de_saida.txt] [tamanho_maximo_da_senha]')
        sys.exit(1)

    caminho_entrada = sys.argv[1]
    if not os.path.isfile(caminho_entrada):
        print(f'Erro: arquivo não encontrado: {caminho_entrada}')
        sys.exit(1)
    if len(sys.argv) >= 3:
        caminho_saida = sys.argv[2]
    else:
        caminho_saida = 'texto_decifrado.txt'
    if len(sys.argv) >= 4:
        # isdecimal (e não isdigit): só aceita dígitos que int() sabe converter.
        if not sys.argv[3].isdecimal() or int(sys.argv[3]) < 1:
            print(f'Erro: o tamanho máximo da senha deve ser um número inteiro >= 1 (recebi "{sys.argv[3]}").')
            sys.exit(1)
        tamanho_maximo = int(sys.argv[3])
    else:
        tamanho_maximo = TAMANHO_MAXIMO_PADRAO

    inicio = time.perf_counter()

    # Entrada (higienizada, para ignorar quebras de linha e afins)
    texto_cifrado = higienizar_texto(ler_arquivo(caminho_entrada))
    if texto_cifrado == '':
        print(f'Erro: o arquivo {caminho_entrada} não tem nenhuma letra de a a z.')
        sys.exit(1)
    print(f'Arquivo cifrado lido: {caminho_entrada} ({len(texto_cifrado)} letras após higienização)')

    # Não faz sentido testar uma senha maior que o próprio texto
    # (sobrariam subtextos vazios).
    if tamanho_maximo > len(texto_cifrado):
        tamanho_maximo = len(texto_cifrado)

    # Etapa 1 - Descoberta do tamanho da senha
    tabela_ic = calcular_tabela_ic(texto_cifrado, tamanho_maximo)
    tamanho_senha = escolher_tamanho_senha(tabela_ic)
    imprimir_tabela_ic(tabela_ic, tamanho_senha)

    # Aviso 1: a senha provavelmente é maior que o máximo testado. (Não pega
    # todos os casos: um DIVISOR da senha pode passar de 0,06 sem aviso; ex.:
    # "criptografia" com máximo 10 escolhe 6, com IC 0,0625.)
    ic_escolhido = tabela_ic[tamanho_senha - 1][1]
    if ic_escolhido < LIMIAR_PARECE_PORTUGUES:
        print(f'AVISO: nenhum tamanho até {tamanho_maximo} deu IC de português (>= {LIMIAR_PARECE_PORTUGUES:.2f}).')
        print('       A senha pode ser maior que isso: tente aumentar o tamanho máximo (3º argumento).')
        print()

    # Aviso 2: texto curto demais. Nesse caso o IC dos subtextos é ruidoso e
    # costuma passar de 0,06 por acaso, então o aviso 1 não ajuda; olhamos
    # direto quantas letras sobram por posição da senha.
    if len(texto_cifrado) < MINIMO_LETRAS_POR_POSICAO * tamanho_senha:
        print(f'AVISO: texto curto: só {len(texto_cifrado) // tamanho_senha} letra(s) por posição da senha (o recomendado é pelo menos {MINIMO_LETRAS_POR_POSICAO}).')
        print('       Com tão pouca estatística, a senha e o texto decifrado podem sair errados.')
        print()

    # Etapa 2 - Análise de frequência
    senha = descobrir_senha(texto_cifrado, tamanho_senha)
    imprimir_tabela_senha(texto_cifrado, senha)
    texto_decifrado = aplicar_deslocamento_inverso(texto_cifrado, senha)

    # Saída
    salvar_arquivo(caminho_saida, texto_decifrado)
    duracao = time.perf_counter() - inicio

    print('Resultado')
    print(f'  Tamanho estimado da senha: {tamanho_senha}')
    print(f'  Senha recuperada .........: {senha}')
    print(f'  Início do texto decifrado : {texto_decifrado[:120]}')
    print(f'  Texto decifrado salvo em .: {caminho_saida}')
    print(f'  Tempo total do ataque ....: {duracao:.2f} s (ler + higienizar + atacar + salvar)')


if __name__ == '__main__':
    main()
