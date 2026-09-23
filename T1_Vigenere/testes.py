"""
testes.py  -  ROTEIRO DE TESTES de cifrar.py e quebrar.py

Uso:
    python3 testes.py <DomCasmurro.txt>

O roteiro higieniza o livro uma vez e, para cada senha de teste:
    1. cifra com a senha;
    2. ataca o texto cifrado SEM usar a senha;
    3. confere se o texto recuperado é IDÊNTICO ao original higienizado
       e mede o tempo do ataque.

Também repete o teste com trechos curtos do livro, para mostrar até onde
a estatística ainda funciona. Tudo é feito em memória: nenhum arquivo é
gravado.
"""

import sys
import time

from higienizacao import ler_arquivo, higienizar_texto
from cifrar import higienizar_senha, cifrar_vigenere
from quebrar import (TAMANHO_MAXIMO_PADRAO, calcular_tabela_ic, escolher_tamanho_senha,
                     descobrir_senha, aplicar_deslocamento_inverso)


def atacar(texto_cifrado):
    """As duas etapas do ataque (as mesmas de quebrar.py). Devolve (tamanho, senha, texto, segundos)."""
    inicio = time.perf_counter()
    tabela_ic = calcular_tabela_ic(texto_cifrado, TAMANHO_MAXIMO_PADRAO)   # Etapa 1
    tamanho = escolher_tamanho_senha(tabela_ic)
    senha = descobrir_senha(texto_cifrado, tamanho)                        # Etapa 2
    texto = aplicar_deslocamento_inverso(texto_cifrado, senha)
    segundos = time.perf_counter() - inicio
    return tamanho, senha, texto, segundos


def testar(descricao, texto_original, senha_digitada):
    """Cifra, ataca e compara. Devolve True se o texto recuperado for idêntico."""
    senha = higienizar_senha(senha_digitada)
    texto_cifrado = cifrar_vigenere(texto_original, senha)
    tamanho, senha_encontrada, texto_recuperado, segundos = atacar(texto_cifrado)
    identico = (texto_recuperado == texto_original)

    print(f'{descricao:<34} letras={len(texto_original):7d} senha={senha:<22} '
          f'-> tamanho={tamanho:2d} senha={senha_encontrada:<22} idêntico={str(identico):<5} tempo={segundos:.2f}s')
    return identico


def main():
    if len(sys.argv) < 2:
        print('Uso: python3 testes.py <DomCasmurro.txt>')
        sys.exit(1)

    livro = higienizar_texto(ler_arquivo(sys.argv[1]))
    print(f'Livro higienizado: {len(livro)} letras')
    print()

    resultados = []

    print('--- livro completo, várias senhas ---')
    for senha in ['segredo', 'criptografia', 'a', 'pucrs', 'abcabc', 'banana', 'abcabd',
                  'machadodeassis', 'Segurança de Sistemas', 'universidadecatolica']:
        resultados.append(testar('livro completo', livro, senha))
    print()

    print('--- trechos curtos do livro (senhas "segredo" e "criptografia") ---')
    for quantidade in [2000, 1000, 500]:
        resultados.append(testar(f'início do livro, {quantidade} letras', livro[:quantidade], 'segredo'))
    resultados.append(testar('meio do livro, 2000 letras', livro[150000:152000], 'segredo'))
    resultados.append(testar('início do livro, 2000 letras', livro[:2000], 'criptografia'))
    print()

    total = len(resultados)
    aprovados = resultados.count(True)
    print(f'Resultado: {aprovados} de {total} testes com texto recuperado idêntico ao original.')


if __name__ == '__main__':
    main()
