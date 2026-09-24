"""
higienizacao.py - Passo 1: higienização do texto (usado por cifrar.py e quebrar.py).

Uso (opcional, para conferência):
    python3 higienizacao.py <arquivo.txt> [arquivo_de_saida.txt]
"""

import os
import sys
import unicodedata

ALFABETO = 'abcdefghijklmnopqrstuvwxyz'


def letra_para_numero(letra):
    """'a' -> 0, 'b' -> 1, ..., 'z' -> 25."""
    return ord(letra) - ord('a')


def numero_para_letra(numero):
    """0 -> 'a', 1 -> 'b', ..., 25 -> 'z'."""
    return ALFABETO[numero]


def ler_arquivo(caminho):
    """Lê o arquivo em UTF-8 (ignorando o BOM); se não for UTF-8, lê como Latin-1."""
    try:
        with open(caminho, encoding='utf-8-sig') as arquivo:
            return arquivo.read()
    except UnicodeDecodeError:
        print(f'Aviso: {caminho} não está em UTF-8; lendo como Latin-1.')
        with open(caminho, encoding='latin-1') as arquivo:
            return arquivo.read()


def salvar_arquivo(caminho, texto):
    try:
        with open(caminho, 'w', encoding='utf-8') as arquivo:
            arquivo.write(texto)
    except OSError as erro:
        print(f'Erro: não foi possível gravar o arquivo {caminho} ({erro.strerror}).')
        sys.exit(1)


def higienizar_texto(texto):
    """
    Deixa só letras minúsculas de a a z. Ex.: "Olá, mundo! 123" -> "olamundo".

    NFD separa a letra do acento ('ç' -> 'c' + '¸'); depois de lower(), só os
    caracteres entre 'a' e 'z' são mantidos, o que descarta acentos, espaços,
    pontuação, números e símbolos.
    """
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.lower()

    letras = []
    for caractere in texto:
        if 'a' <= caractere <= 'z':
            letras.append(caractere)
    return ''.join(letras)


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
