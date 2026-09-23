# T1 – Cifra de Vigenère e Criptoanálise (Segurança de Sistemas, PUCRS)

Implementação em **Python 3, só biblioteca padrão** (nenhuma instalação
extra), de:

1. **Criptografia** com a Cifra de Vigenère (`cifrar.py`);
2. **Criptoanálise** que recupera o texto original **sem conhecer a senha**
   (`quebrar.py`), assumindo texto em português.

O código está organizado na mesma ordem do enunciado e comentado para ser
lido como um livro-texto: cada função faz uma coisa só e os comentários
explicam a ideia matemática por trás.

## Arquivos

| Arquivo           | Seção do enunciado                                                          |
|-------------------|-----------------------------------------------------------------------------|
| `higienizacao.py` | Passo 1 – Higienização (+ alfabeto, letra ↔ número, leitura/gravação)       |
| `cifrar.py`       | Parte 1 – Criptografia com a Cifra de Vigenère                              |
| `quebrar.py`      | Parte 2 – Criptoanálise: Etapa 1 (IC) e Etapa 2 (análise de frequência)     |
| `testes.py`       | Roteiro de testes: cifra, ataca e compara com o original (tudo em memória)  |

`texto_criptografado.txt` e `texto_decifrado.txt` são exemplos gerados com o
Dom Casmurro e a senha `segredo`.

## Como rodar

Os exemplos assumem que `DomCasmurro.txt` está na pasta de cima
(`../DomCasmurro.txt`); troque pelo caminho do seu arquivo.

```bash
# Parte 1 – cifrar (gera texto_criptografado.txt)
python3 cifrar.py ../DomCasmurro.txt segredo

# Parte 2 – quebrar SEM informar a senha (gera texto_decifrado.txt)
python3 quebrar.py texto_criptografado.txt

# Conferir que o texto recuperado é idêntico ao original higienizado
python3 higienizacao.py ../DomCasmurro.txt        # gera texto_higienizado.txt
cmp texto_higienizado.txt texto_decifrado.txt && echo IDENTICOS
rm texto_higienizado.txt                           # só servia para a conferência

# Roteiro completo de testes (várias senhas, trechos curtos, tempo de cada ataque)
python3 testes.py ../DomCasmurro.txt
```

Formas gerais:

```
python3 cifrar.py  <arquivo_original.txt> [senha] [arquivo_de_saida.txt]
python3 quebrar.py <texto_criptografado.txt> [arquivo_de_saida.txt] [tamanho_maximo_da_senha]
```

- Em `cifrar.py`, se a senha não vier na linha de comando ela é pedida no
  teclado. A senha é higienizada como o texto: `"Segrêdo 123"` vira `segredo`.
  Senha com espaços precisa de aspas: `"Segurança de Sistemas"` (sem aspas o
  programa recebe argumentos demais e avisa).
- Em `quebrar.py`, por padrão são testados tamanhos de senha de 1 a 20. O 2º
  argumento é sempre o arquivo de saída, então para mudar o máximo é preciso
  passar os dois (ex.: `python3 quebrar.py texto_criptografado.txt saida.txt 30`).
- Sem argumentos, cada programa imprime a mensagem de uso. Arquivo
  inexistente, arquivo sem letras, senha sem letras (ou entrada fechada no
  prompt da senha), argumentos demais, tamanho máximo inválido ou arquivo de
  saída que não pode ser gravado geram uma mensagem de erro clara (código de
  saída 1).
- Os arquivos de entrada devem estar em UTF-8 (com ou sem BOM); um arquivo
  que não seja UTF-8 é lido como Latin-1, com um aviso. UTF-16 não é suportado.

## O que o programa imprime

`cifrar.py` mostra quantos caracteres foram lidos, quantas letras sobraram
após a higienização, a senha usada (já higienizada) e o início do texto
limpo e do texto cifrado.

`quebrar.py` mostra, nesta ordem:

1. a **tabela de IC por tamanho de senha** (com barra visual) e a marca
   `<-- tamanho escolhido`;
2. a **tabela da Etapa 2**, posição por posição: quantas letras tem o
   subtexto, a letra mais comum nele (ainda cifrada), o deslocamento
   encontrado e a letra da senha;
3. o **resultado**: tamanho estimado, senha recuperada, início do texto
   decifrado, arquivo gravado e tempo total do ataque.

Entre a tabela de IC e a Etapa 2 podem aparecer dois avisos: nenhum tamanho
testado deu IC de português (a senha provavelmente é maior que o máximo) ou
texto curto demais (menos de 70 letras por posição da senha).

No Dom Casmurro do Project Gutenberg as ~930 primeiras letras são o cabeçalho
em inglês, e é isso que aparece no "início do texto decifrado"; o português
começa logo depois (`cut -c 939-1060 texto_decifrado.txt` mostra
`umanoitedestasvindodacidadeparaoengenhonovo...`).

Exemplo real (Dom Casmurro, senha `segredo`, trecho da saída):

```
  Tamanho   IC médio
        6   0.0468  #######################
        7   0.0768  ######################################  <-- tamanho escolhido
        8   0.0468  #######################
       ...
       14   0.0768  ######################################

  Posição   Letras   Mais comum (cifrado)   Deslocamento   Letra da senha
        1    44127            s                       18         s
        2    44127            e                        4         e
       ...
  Tamanho estimado da senha: 7
  Senha recuperada .........: segredo
  Tempo total do ataque ....: 0.15 s (ler + higienizar + atacar + salvar)
```

## Como funciona

**Higienização (Passo 1).** `unicodedata.normalize('NFD', texto)` separa
cada letra acentuada em letra base + acento (`ã` → `a` + `~`, `ç` → `c` + `¸`);
`.lower()` põe tudo em minúsculas; um laço guarda só os caracteres entre `'a'`
e `'z'`, o que descarta de uma vez acentos soltos, espaços, quebras de linha,
pontuação, números, símbolos e o BOM do arquivo. (Usa-se NFD, e não NFKD,
porque NFKD converteria símbolos em letras: `™` → `tm`, `ª` → `a`.) No Dom
Casmurro sobram 308.887 letras.

**Cifra de Vigenère (Parte 1).** As letras viram números (`a=0 … z=25`). A
senha é repetida ciclicamente e cada letra do texto é somada, módulo 26, à
letra da senha que ficou embaixo dela:

```
cifrado[i] = (texto[i] + senha[i mod T]) mod 26          T = tamanho da senha
```

Exemplo: `ataque` + `segredo` → `a+s = 0+18 = 18 → s`, `t+e = 19+4 = 23 → x`,
`a+g = 6 → g`, `q+r = 16+17 = 33 mod 26 = 7 → h`, … = `sxghyh`. A mesma letra
`a` virou `s` e `g`: é isso que "mistura" as frequências e torna a Vigenère
mais forte que a Cifra de César.

**Etapa 1 – tamanho da senha (Índice de Coincidência).** O IC é a
probabilidade de duas letras sorteadas ao acaso no texto serem iguais:

```
IC = soma( n_i · (n_i − 1) ) / ( N · (N − 1) )
```

Em português o IC é ≈ 0,077 (a, e, o, s são muito frequentes); em letras
"embaralhadas" cai para 1/26 ≈ 0,038. Uma Cifra de César não muda o IC (só
troca os nomes das letras), mas a Vigenère mistura várias Césares e derruba
o IC. Então, para cada tamanho T de 1 a 20, dividimos o texto cifrado em T
subtextos (posições `i, i+T, i+2T, …`) e calculamos o IC médio: no T certo
cada subtexto é uma César pura e o IC volta a ≈ 0,077; nos T errados fica
≈ 0,047.

*Armadilha dos múltiplos:* para a senha `segredo` (7), os tamanhos 14 e 21
também dão IC ≈ 0,077 (dividir em 14 subtextos ainda deixa cada um com um só
deslocamento). Por isso **não** se pega simplesmente o maior IC: a regra é
escolher o **menor tamanho cujo IC chega a 95 % do maior IC da tabela**.
Usa-se uma fração do máximo, e não um limiar fixo, porque um *divisor* do
tamanho certo pode ter IC "meio alto" (`criptografia`, 12 letras: IC(6) =
0,0625, pois o subtexto `(r,r)` é uma César pura); e a margem é 95 %, e não
90 %, porque senhas com letras repetidas em posições regulares sobem ainda
mais o divisor (`banana`: IC(2) = 92 % de IC(6)).

**Etapa 2 – letras da senha (análise de frequência).** Cada subtexto é uma
César com deslocamento desconhecido. Contamos as 26 letras do subtexto uma
vez e, para cada um dos 26 deslocamentos possíveis, "giramos" a contagem
(desfazendo o deslocamento) e medimos o encaixe com a tabela de frequências
do português pelo produto escalar entre as duas distribuições: se os picos
do texto (a, e, o, s) caem sobre os picos da tabela, a soma fica alta. O
deslocamento de maior pontuação é a letra da senha (`0 = a, 1 = b, …`). O
qui-quadrado também funcionaria, mas divide pela frequência esperada e
letras raríssimas (k, w, y ≈ 0,01 %) fazem a conta explodir em textos
curtos; o produto escalar não tem esse problema.

**Reconstrução.** Com a senha, aplica-se o deslocamento inverso
(`original[i] = (cifrado[i] − senha[i mod T]) mod 26`; em Python
`(-3) % 26 == 23`, então o "dar a volta" sai de graça).

**Desempenho.** Tudo é O(n): contagem de letras com `str.count` (em C),
subtextos com fatias `texto[i::T]`, strings montadas com lista + `''.join`.
Dom Casmurro inteiro é quebrado em ≈ 0,15 s; dez cópias concatenadas
(3,09 milhões de letras) em ≈ 1,4 s.

## Resultados medidos (Dom Casmurro, 308.887 letras após higienização)

| Senha                      | Tamanho achado | Senha recuperada       | Texto idêntico | Tempo do ataque |
|----------------------------|----------------|------------------------|----------------|-----------------|
| segredo                    | 7              | segredo                | sim            | 0,12 s          |
| criptografia (12 letras)   | 12             | criptografia           | sim            | 0,11 s          |
| a (1 letra)                | 1              | a                      | sim            | 0,11 s          |
| pucrs                      | 5              | pucrs                  | sim            | 0,12 s          |
| abcabc (período real 3)    | 3              | abc                    | sim            | 0,11 s          |
| banana                     | 6              | banana                 | sim            | 0,12 s          |
| abcabd                     | 6              | abcabd                 | sim            | 0,12 s          |
| machadodeassis             | 14             | machadodeassis         | sim            | 0,12 s          |
| Segurança de Sistemas      | 19             | segurancadesistemas    | sim            | 0,12 s          |
| universidadecatolica       | 20             | universidadecatolica   | sim            | 0,12 s          |
| segredo, só 2000 letras    | 7              | segredo                | sim            | < 0,01 s        |
| segredo, só 1000 letras    | 7              | segredo                | sim            | < 0,01 s        |
| segredo, só 500 letras     | 7              | segredo                | sim            | < 0,01 s        |
| meio do livro, 2000 letras | 7              | segredo                | sim            | < 0,01 s        |
| criptografia, 2000 letras  | 12             | criptografia           | sim            | < 0,01 s        |

Pela linha de comando (ler + higienizar + atacar + salvar) `quebrar.py` leva
≈ 0,15 s no livro inteiro. Uma senha de 29 letras é encontrada com o terceiro
argumento `30`; com o padrão 20 o programa avisa que nenhum tamanho parece
português.

## Limitações conhecidas

- O ataque assume texto em **português** (tabela de frequências e IC de
  referência). Trechos em inglês, como o cabeçalho do Project Gutenberg,
  podem confundir a análise de frequência se dominarem um arquivo curto.
- Precisa de texto suficiente: na prática ≈ 70 letras por posição da senha
  (≈ 500 letras para uma senha de 7). Com menos (ex.: 300 letras), uma letra
  da senha pode sair errada e a regra dos 95 % pode escolher um múltiplo do
  tamanho real (o texto ainda decifra, mas a senha aparece repetida). O
  programa avisa quando sobram menos de 70 letras por posição.
- Só testa tamanhos até o máximo informado (20 por padrão). Aumentar muito o
  máximo deixa o IC de textos curtos mais ruidoso, por isso o padrão é 20. Se
  a senha for maior que o máximo, normalmente nenhum tamanho passa de IC 0,06
  e o programa avisa; mas um *divisor* da senha pode passar sem aviso (ex.:
  `criptografia` com máximo 10 escolhe 6, IC 0,0625, e decifra errado).
- Senha que é repetição de outra (`abcabc`) é reportada pelo período real
  (`abc`): o texto decifra corretamente, só o "tamanho" difere do digitado.
- Senhas patológicas, quase todas de uma mesma letra (`aaaaaaaaaaaaaaaaaaab`)
  ou repetição quase perfeita (`xyzxyzxyzxya`), são confundidas com um período
  menor. Senhas comuns com letras repetidas (`banana`, `casa`, `arara`,
  `abcabd`, `aaaaaaab`) são recuperadas corretamente.
- O arquivo inteiro é carregado na memória (para um livro isso são poucos MB).
