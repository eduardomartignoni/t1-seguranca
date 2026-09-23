"""
higienizacao.py  -  PASSO 1 DO ENUNCIADO: HIGIENIZAÇÃO DO TEXTO
(módulo compartilhado por cifrar.py e quebrar.py)

O enunciado exige que o texto seja "limpo" antes de qualquer coisa:
    - converter tudo para minúsculas;
    - remover acentos (á -> a, ç -> c, ã -> a, ...);
    - remover pontuação, números, espaços e caracteres especiais;
    - manter apenas as letras de a a z.

Esse mesmo tratamento é aplicado:
    - ao texto original (antes de cifrar);
    - à senha digitada pelo usuário;
    - ao arquivo cifrado (antes de atacar), o que deixa o ataque robusto a
      quebras de linha ou qualquer "lixo" que exista no arquivo.

Aqui também ficam as pequenas funções que os dois programas compartilham:
a conversão letra <-> número (a cifra trabalha com números de 0 a 25) e a
leitura/gravação de arquivos.

Uso direto (opcional, apenas para conferência):
    python3 higienizacao.py <arquivo.txt> [arquivo_de_saida.txt]

    Grava o texto higienizado (padrão: texto_higienizado.txt). Serve para
    comparar, byte a byte, o original higienizado com o texto que o ataque
    recupera (ver README.md).
"""

import os
import sys
import unicodedata

# Alfabeto de 26 letras usado em todo o trabalho (posição 0 = 'a', 25 = 'z').
ALFABETO = 'abcdefghijklmnopqrstuvwxyz'


# ============================================================================
# ARITMÉTICA DO ALFABETO: cada letra vira um número de 0 a 25 e vice-versa
# ============================================================================

def letra_para_numero(letra):
    """'a' -> 0, 'b' -> 1, ..., 'z' -> 25   (ord('a') vale 97, ord('b') 98...)."""
    return ord(letra) - ord('a')


def numero_para_letra(numero):
    """0 -> 'a', 1 -> 'b', ..., 25 -> 'z'."""
    return ALFABETO[numero]


# ============================================================================
# LEITURA E GRAVAÇÃO DE ARQUIVOS
# ============================================================================

def ler_arquivo(caminho):
    """
    Lê o arquivo inteiro para a memória e devolve o conteúdo como texto.

    Primeiro tenta UTF-8 ('utf-8-sig' também descarta o BOM, uma marca
    invisível que alguns editores colocam no início do arquivo; o próprio
    DomCasmurro.txt tem uma). Se o arquivo não for UTF-8 (arquivos antigos
    em português costumam ser Latin-1), avisa e tenta Latin-1, que aceita
    qualquer sequência de bytes. O aviso importa porque a queda vale para o
    arquivo INTEIRO: um único byte inválido em um arquivo UTF-8 faria todos
    os acentos serem lidos errado sem que ninguém percebesse.
    """
    try:
        with open(caminho, encoding='utf-8-sig') as arquivo:
            return arquivo.read()
    except UnicodeDecodeError:
        print(f'Aviso: {caminho} não está em UTF-8; lendo como Latin-1.')
        with open(caminho, encoding='latin-1') as arquivo:
            return arquivo.read()


def salvar_arquivo(caminho, texto):
    """
    Grava o texto no arquivo indicado (sobrescreve se já existir).
    Se não der para gravar (pasta inexistente, sem permissão...), avisa e para.
    """
    try:
        with open(caminho, 'w', encoding='utf-8') as arquivo:
            arquivo.write(texto)
    except OSError as erro:
        print(f'Erro: não foi possível gravar o arquivo {caminho} ({erro.strerror}).')
        sys.exit(1)


# ============================================================================
# PASSO 1 - HIGIENIZAÇÃO
# ============================================================================

def higienizar_texto(texto):
    """
    Devolve o texto contendo somente letras minúsculas de a a z.

    Como funciona:
      1. unicodedata.normalize('NFD', ...) "desmonta" cada letra acentuada
         em duas partes: a letra base + o sinal de acento.
         Exemplo:  'ç' vira 'c' + '¸'   e   'ã' vira 'a' + '~'.
         (NFD = decomposição canônica. A variante NFKD também transformaria
         símbolos em letras, como '™' -> 'tm' e 'ª' -> 'a', e o enunciado
         manda REMOVER símbolos, não convertê-los em letras.)
      2. .lower() passa tudo para minúsculas (inclusive 'É' -> 'é' -> 'e').
      3. O laço final guarda apenas os caracteres entre 'a' e 'z'. Com isso
         somem, de uma vez só: os sinais de acento separados no passo 1,
         espaços, quebras de linha, pontuação, números e símbolos.

    Exemplo: "Olá, mundo! 123" -> "olamundo"

    Observação de desempenho: as letras são acumuladas em uma lista e unidas
    no final com ''.join(). Concatenar strings dentro do laço ("texto += c")
    seria muito lento em arquivos grandes, porque cada soma copia o texto
    inteiro de novo.
    """
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.lower()

    letras = []
    for caractere in texto:
        if 'a' <= caractere <= 'z':
            letras.append(caractere)
    return ''.join(letras)


# ============================================================================
# PROGRAMA PRINCIPAL (opcional: só higieniza um arquivo, para conferência)
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print('Uso: python3 higienizacao.py <arquivo.txt> [arquivo_de_saida.txt]')
        print('Exemplo: python3 higienizacao.py ../DomCasmurro.txt')
        sys.exit(1)

    caminho_entrada = sys.argv[1]
    if not os.path.isfile(caminho_entrada):
        print(f'Erro: arquivo não encontrado: {caminho_entrada}')
        sys.exit(1)
    if len(sys.argv) >= 3:
        caminho_saida = sys.argv[2]
    else:
        caminho_saida = 'texto_higienizado.txt'

    texto_original = ler_arquivo(caminho_entrada)
    texto_limpo = higienizar_texto(texto_original)
    salvar_arquivo(caminho_saida, texto_limpo)

    print(f'Arquivo lido ..............: {caminho_entrada} ({len(texto_original)} caracteres)')
    print(f'Letras após higienização ..: {len(texto_limpo)}')
    print(f'Início do texto higienizado: {texto_limpo[:60]}')
    print(f'Texto higienizado salvo em : {caminho_saida}')


if __name__ == '__main__':
    main()
