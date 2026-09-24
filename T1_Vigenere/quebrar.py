"""
quebrar.py - Parte 2: criptoanálise da Cifra de Vigenère, sem conhecer a senha
(texto em português).

Uso:
    python3 quebrar.py <texto_criptografado.txt> [arquivo_de_saida.txt] [tamanho_maximo_da_senha]

Saída padrão: texto_decifrado.txt. Tamanhos testados por padrão: 1 a 20.

Etapa 1 - o Índice de Coincidência (IC) estima o tamanho T da senha.
Etapa 2 - as letras nas posições i, i+T, i+2T... foram cifradas pela mesma
          letra da senha (uma Cifra de César); cada uma é descoberta por
          análise de frequência.
"""

import os
import sys
import time

from higienizacao import (ALFABETO, ler_arquivo, salvar_arquivo, higienizar_texto,
                          letra_para_numero, numero_para_letra)

# Testar tamanhos muito grandes deixa os subtextos pequenos e o IC ruidoso.
TAMANHO_MAXIMO_PADRAO = 20


def contar_letras(texto):
    """Lista de 26 contagens: [quantos 'a', quantos 'b', ..., quantos 'z']."""
    # str.count roda em C: bem mais rápido que um laço em Python (arquivos grandes).
    contagem = []
    for letra in ALFABETO:
        contagem.append(texto.count(letra))
    return contagem


# ============================================================================
# ETAPA 1 - TAMANHO DA SENHA (ÍNDICE DE COINCIDÊNCIA)
# ============================================================================
# IC = probabilidade de duas letras sorteadas do texto serem iguais:
# ~0,077 em português e ~0,038 (1/26) em texto aleatório. A Vigenère mistura
# várias Césares e derruba o IC; com o tamanho T certo, cada subtexto é uma
# César pura e o IC médio volta a ~0,077.

IC_PORTUGUES = 0.077
IC_ALEATORIO = 1 / 26
LIMIAR_PARECE_PORTUGUES = 0.06   # entre o IC aleatório e o do português
MARGEM_DO_MAXIMO = 0.95
MINIMO_LETRAS_POR_POSICAO = 70   # com menos, a Etapa 2 começa a errar letras


def indice_de_coincidencia(texto):
    """IC = soma(n_i * (n_i - 1)) / (N * (N - 1))"""
    total = len(texto)
    if total < 2:
        return 0.0

    contagem = contar_letras(texto)
    soma = 0
    for n_i in contagem:
        soma += n_i * (n_i - 1)
    return soma / (total * (total - 1))


def dividir_em_subtextos(texto, tamanho):
    """Subtexto i = letras das posições i, i+tamanho, i+2*tamanho, ..."""
    subtextos = []
    for i in range(tamanho):
        subtextos.append(texto[i::tamanho])
    return subtextos


def ic_medio_dos_subtextos(texto, tamanho):
    subtextos = dividir_em_subtextos(texto, tamanho)
    soma = 0.0
    for subtexto in subtextos:
        soma += indice_de_coincidencia(subtexto)
    return soma / tamanho


def calcular_tabela_ic(texto, tamanho_maximo):
    """Pares (tamanho, IC médio) para tamanho = 1..tamanho_maximo."""
    tabela = []
    for tamanho in range(1, tamanho_maximo + 1):
        tabela.append((tamanho, ic_medio_dos_subtextos(texto, tamanho)))
    return tabela


def escolher_tamanho_senha(tabela):
    """
    Escolhe o MENOR tamanho cujo IC chega a 95% do maior IC da tabela.

    Não basta pegar o maior IC: os múltiplos do tamanho certo (14, 21... para
    "segredo") também dão IC alto. E a margem de 95% descarta divisores com
    IC "meio alto" (ex.: "banana" -> IC(2) = 92% de IC(6)).
    """
    maior_ic = 0.0
    for tamanho, ic in tabela:
        if ic > maior_ic:
            maior_ic = ic

    for tamanho, ic in tabela:
        if ic >= MARGEM_DO_MAXIMO * maior_ic:
            return tamanho


def imprimir_tabela_ic(tabela, tamanho_escolhido):
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
# Para cada subtexto testam-se os 26 deslocamentos possíveis; vence o que
# deixa as frequências mais parecidas com as do português.

# Frequência das letras em português (%).
FREQUENCIA_PORTUGUES_PORCENTO = {
    'a': 14.63, 'b': 1.04, 'c': 3.88, 'd': 4.99, 'e': 12.57, 'f': 1.02,
    'g': 1.30, 'h': 1.28, 'i': 6.18, 'j': 0.40, 'k': 0.02, 'l': 2.78,
    'm': 4.74, 'n': 5.05, 'o': 10.73, 'p': 2.52, 'q': 1.20, 'r': 6.53,
    's': 7.81, 't': 4.34, 'u': 4.63, 'v': 1.67, 'w': 0.01, 'x': 0.21,
    'y': 0.01, 'z': 0.47,
}


def montar_frequencia_esperada():
    """Converte a tabela em % para 26 frequências (0 = 'a') que somam 1."""
    soma_da_tabela = sum(FREQUENCIA_PORTUGUES_PORCENTO.values())
    frequencias = []
    for letra in ALFABETO:
        frequencias.append(FREQUENCIA_PORTUGUES_PORCENTO[letra] / soma_da_tabela)
    return frequencias


FREQUENCIA_ESPERADA = montar_frequencia_esperada()


def pontuacao_de_encaixe(contagem_observada, total_letras):
    """
    Produto escalar entre a frequência observada e a do português.
    Quanto maior, mais o texto se parece com português.
    """
    pontuacao = 0.0
    for i in range(26):
        frequencia_observada = contagem_observada[i] / total_letras
        pontuacao += frequencia_observada * FREQUENCIA_ESPERADA[i]
    return pontuacao


def descobrir_deslocamento(subtexto):
    """
    Devolve o deslocamento (0 a 25) que deixa o subtexto mais parecido com
    português. As letras são contadas uma vez só: com deslocamento d, a letra
    original i aparece no cifrado como (i + d) mod 26, então basta "girar" a
    contagem.
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
    """Um deslocamento por posição da senha; deslocamento 0 = 'a', 1 = 'b', ..."""
    subtextos = dividir_em_subtextos(texto_cifrado, tamanho_senha)
    letras_da_senha = []
    for subtexto in subtextos:
        deslocamento = descobrir_deslocamento(subtexto)
        letras_da_senha.append(numero_para_letra(deslocamento))
    return ''.join(letras_da_senha)


def imprimir_tabela_senha(texto_cifrado, senha):
    """Por posição: tamanho do subtexto, letra mais comum (cifrada), deslocamento e letra da senha."""
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
    """original[i] = (cifrado[i] - senha[i mod tamanho_da_senha]) mod 26"""
    tamanho_senha = len(senha)
    resultado = []

    for i in range(len(texto_cifrado)):
        numero_cifrado = letra_para_numero(texto_cifrado[i])
        numero_senha = letra_para_numero(senha[i % tamanho_senha])
        numero_original = (numero_cifrado - numero_senha) % 26
        resultado.append(numero_para_letra(numero_original))

    return ''.join(resultado)


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
        if not sys.argv[3].isdecimal() or int(sys.argv[3]) < 1:
            print(f'Erro: o tamanho máximo da senha deve ser um número inteiro >= 1 (recebi "{sys.argv[3]}").')
            sys.exit(1)
        tamanho_maximo = int(sys.argv[3])
    else:
        tamanho_maximo = TAMANHO_MAXIMO_PADRAO

    inicio = time.perf_counter()

    texto_cifrado = higienizar_texto(ler_arquivo(caminho_entrada))
    if texto_cifrado == '':
        print(f'Erro: o arquivo {caminho_entrada} não tem nenhuma letra de a a z.')
        sys.exit(1)
    print(f'Arquivo cifrado lido: {caminho_entrada} ({len(texto_cifrado)} letras após higienização)')

    # A senha não pode ser maior que o próprio texto.
    if tamanho_maximo > len(texto_cifrado):
        tamanho_maximo = len(texto_cifrado)

    # Etapa 1 - Tamanho da senha
    tabela_ic = calcular_tabela_ic(texto_cifrado, tamanho_maximo)
    tamanho_senha = escolher_tamanho_senha(tabela_ic)
    imprimir_tabela_ic(tabela_ic, tamanho_senha)

    ic_escolhido = tabela_ic[tamanho_senha - 1][1]
    if ic_escolhido < LIMIAR_PARECE_PORTUGUES:
        print(f'AVISO: nenhum tamanho até {tamanho_maximo} deu IC de português (>= {LIMIAR_PARECE_PORTUGUES:.2f}).')
        print('       A senha pode ser maior que isso: tente aumentar o tamanho máximo (3º argumento).')
        print()

    if len(texto_cifrado) < MINIMO_LETRAS_POR_POSICAO * tamanho_senha:
        print(f'AVISO: texto curto: só {len(texto_cifrado) // tamanho_senha} letra(s) por posição da senha (o recomendado é pelo menos {MINIMO_LETRAS_POR_POSICAO}).')
        print('       Com tão pouca estatística, a senha e o texto decifrado podem sair errados.')
        print()

    # Etapa 2 - Análise de frequência
    senha = descobrir_senha(texto_cifrado, tamanho_senha)
    imprimir_tabela_senha(texto_cifrado, senha)
    texto_decifrado = aplicar_deslocamento_inverso(texto_cifrado, senha)

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
