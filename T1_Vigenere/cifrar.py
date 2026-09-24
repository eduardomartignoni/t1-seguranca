"""
cifrar.py - Parte 1: criptografia com a Cifra de Vigenère.

Uso:
    python3 cifrar.py <arquivo_original.txt> [senha] [arquivo_de_saida.txt]

Sem a senha na linha de comando, ela é pedida no teclado.
Saída padrão: texto_criptografado.txt
"""

import os
import sys

from higienizacao import (ler_arquivo, salvar_arquivo, higienizar_texto,
                          letra_para_numero, numero_para_letra)


def higienizar_senha(senha):
    """A senha passa pela mesma higienização do texto: "Segrêdo 123" -> "segredo"."""
    senha_limpa = higienizar_texto(senha)
    if senha_limpa == '':
        print(f'Erro: a senha "{senha}" não tem nenhuma letra de a a z.')
        sys.exit(1)
    return senha_limpa


def cifrar_vigenere(texto, senha):
    """
    cifrado[i] = (texto[i] + senha[i mod tamanho_da_senha]) mod 26

    As letras viram números (a=0, ..., z=25) e a senha se repete ciclicamente.
    Ex.: "ataque" com a senha "segredo" -> "sxghyh".
    """
    tamanho_senha = len(senha)
    resultado = []

    for i in range(len(texto)):
        numero_texto = letra_para_numero(texto[i])
        numero_senha = letra_para_numero(senha[i % tamanho_senha])
        numero_cifrado = (numero_texto + numero_senha) % 26
        resultado.append(numero_para_letra(numero_cifrado))

    return ''.join(resultado)


def main():
    if len(sys.argv) < 2:
        print('Uso: python3 cifrar.py <arquivo_original.txt> [senha] [arquivo_de_saida.txt]')
        print('Exemplo: python3 cifrar.py ../DomCasmurro.txt segredo')
        sys.exit(1)
    if len(sys.argv) > 4:
        print('Erro: argumentos demais. Se a senha tem espaços, coloque-a entre aspas: "Segurança de Sistemas".')
        sys.exit(1)

    caminho_entrada = sys.argv[1]
    if not os.path.isfile(caminho_entrada):
        print(f'Erro: arquivo não encontrado: {caminho_entrada}')
        sys.exit(1)
    if len(sys.argv) >= 3:
        senha_digitada = sys.argv[2]
    else:
        try:
            senha_digitada = input('Digite a senha: ')
        except EOFError:
            print()
            print('Erro: nenhuma senha foi informada.')
            sys.exit(1)
    if len(sys.argv) >= 4:
        caminho_saida = sys.argv[3]
    else:
        caminho_saida = 'texto_criptografado.txt'

    # Passo 1 - Higienização (do texto e da senha)
    texto_original = ler_arquivo(caminho_entrada)
    texto_limpo = higienizar_texto(texto_original)
    if texto_limpo == '':
        print(f'Erro: o arquivo {caminho_entrada} não tem nenhuma letra de a a z.')
        sys.exit(1)
    senha = higienizar_senha(senha_digitada)

    # Passo 2 - Criptografia
    texto_cifrado = cifrar_vigenere(texto_limpo, senha)
    salvar_arquivo(caminho_saida, texto_cifrado)

    print(f'Arquivo lido ............: {caminho_entrada} ({len(texto_original)} caracteres)')
    print(f'Letras após higienização : {len(texto_limpo)}')
    print(f'Senha usada (higienizada): {senha} (tamanho {len(senha)})')
    print(f'Início do texto limpo ...: {texto_limpo[:60]}')
    print(f'Início do texto cifrado .: {texto_cifrado[:60]}')
    print(f'Texto cifrado salvo em ..: {caminho_saida}')


if __name__ == '__main__':
    main()
