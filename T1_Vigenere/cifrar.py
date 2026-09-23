"""
cifrar.py  -  PARTE 1 DO ENUNCIADO: CRIPTOGRAFIA COM A CIFRA DE VIGENÈRE

Uso:
    python3 cifrar.py <arquivo_original.txt> [senha] [arquivo_de_saida.txt]

    - Se a senha não for passada na linha de comando, ela é pedida no teclado.
    - O arquivo de saída padrão é texto_criptografado.txt.

Fluxo (na mesma ordem do enunciado):
    Passo 1 - Higienização do texto ......... higienizar_texto (higienizacao.py)
    Passo 2 - Criptografia (Vigenère) ....... cifrar_vigenere (abaixo)
    Saída   - Salvar o texto cifrado ........ texto_criptografado.txt
"""

import os
import sys

from higienizacao import (ler_arquivo, salvar_arquivo, higienizar_texto,
                          letra_para_numero, numero_para_letra)


# ============================================================================
# ENTRADA: a senha (chave) fornecida pelo usuário
# ============================================================================

def higienizar_senha(senha):
    """
    A senha passa pela MESMA higienização do texto: "Segrêdo 123" vira
    "segredo". Assim a senha só tem letras de a a z, que é o que a cifra usa.
    Se depois da limpeza não sobrar nenhuma letra, o programa avisa e para.
    """
    senha_limpa = higienizar_texto(senha)
    if senha_limpa == '':
        print(f'Erro: a senha "{senha}" não tem nenhuma letra de a a z.')
        sys.exit(1)
    return senha_limpa


# ============================================================================
# PASSO 2 - CRIPTOGRAFIA (CIFRA DE VIGENÈRE)
# ============================================================================

def cifrar_vigenere(texto, senha):
    """
    Cifra de Vigenère = uma Cifra de César diferente para cada posição.

    As letras viram números (a=0, b=1, ..., z=25). A senha é repetida
    ciclicamente ao longo do texto, e cada letra do texto é SOMADA (módulo 26)
    à letra da senha que ficou embaixo dela:

        cifrado[i] = ( texto[i] + senha[i mod tamanho_da_senha] ) mod 26

    O "i mod tamanho_da_senha" é o que faz a senha se repetir: quando i chega
    ao fim da senha, o resto da divisão volta a zero.

    Exemplo com a senha "segredo":
        texto :   a     t     a     q        u     e
        senha :   s     e     g     r        e     d
        soma  :  0+18  19+4   0+6  16+17    20+4   4+3
              =   18    23     6   33%26=7   24     7
        cifra :   s     x     g     h        y     h

    Mini-exemplo do "dar a volta": 'x' + 'e' = 23 + 4 = 27 -> 27 % 26 = 1 -> 'b'.

    Repare que a mesma letra do texto ('a' aparece duas vezes acima) virou
    letras diferentes ('s' e 'g'). É isso que torna a Vigenère mais forte
    que a César: as frequências das letras ficam "misturadas".
    """
    tamanho_senha = len(senha)
    resultado = []

    for i in range(len(texto)):
        numero_texto = letra_para_numero(texto[i])
        numero_senha = letra_para_numero(senha[i % tamanho_senha])
        numero_cifrado = (numero_texto + numero_senha) % 26
        resultado.append(numero_para_letra(numero_cifrado))

    return ''.join(resultado)


# ============================================================================
# PROGRAMA PRINCIPAL
# ============================================================================

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
        except EOFError:   # entrada fechada (Ctrl-D, ou stdin vazio/redirecionado)
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

    # Saída
    salvar_arquivo(caminho_saida, texto_cifrado)

    print(f'Arquivo lido ............: {caminho_entrada} ({len(texto_original)} caracteres)')
    print(f'Letras após higienização : {len(texto_limpo)}')
    print(f'Senha usada (higienizada): {senha} (tamanho {len(senha)})')
    print(f'Início do texto limpo ...: {texto_limpo[:60]}')
    print(f'Início do texto cifrado .: {texto_cifrado[:60]}')
    print(f'Texto cifrado salvo em ..: {caminho_saida}')


if __name__ == '__main__':
    main()
