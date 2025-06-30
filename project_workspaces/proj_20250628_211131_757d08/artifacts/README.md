# Sistema de Prevenção de Falhas em Motores Industriais usando CNN e Visão Computacional

Este repositório contém o código e os documentos necessários para reproduzir o artigo de TCC intitulado "Sistema de Prevenção de Falhas em Motores Industriais usando CNN e Visão Computacional". O artigo foi escrito em LaTeX e está pronto para publicação.

## Introdução

O objetivo deste projeto é desenvolver um sistema de prevenção de falhas em motores industriais utilizando técnicas de aprendizado de máquina (especificamente CNNs) e visão computacional. O sistema analisa imagens de motores para detectar falhas antes que elas causem danos.

## Pré-requisitos

Para compilar o artigo LaTeX, você precisará de:
- LaTeX distribution (TeX Live ou MiKTeX)
- Um editor de LaTeX (opcional, mas recomendado)
- Python (versão 3.6 ou superior) para execução de scripts (se houver)
- Biblioteca NumPy e outras bibliotecas Python (se necessário para processamento de dados)

## Instalação

1. Clone este repositório para sua máquina local.
2. Instale o LaTeX distribution de sua preferência.
3. Instale as dependências do projeto Python (se aplicável) usando:
   ```
pip install -r requirements.txt
   ```

## Uso

Para gerar o PDF do artigo LaTeX, abra o terminal no diretório raiz do projeto e execute:

```
pdflatex -interaction=nonstopmode main.tex
```

Isso gerará um arquivo `main.pdf` que contém o artigo pronto para publicação.

Se houver scripts Python para processamento de dados ou treinamento do modelo, consulte o README correspondente.

## Estrutura do Projeto

A estrutura do projeto é a seguinte:

```
projeto-tcc/
├── main.tex          # Arquivo principal do artigo LaTeX
├── figures/          # Pasta para armazenar imagens e gráficos
│   ├── figure1.pdf
│   ├── figure2.pdf
│   └── ...
├── tables/           # Pasta para armazenar tabelas (se houver)
│   ├── table1.tex
│   └── ...
├── data/             # Pasta para dados (imagens, conjuntos de treinamento, etc.)
│   ├── train/
│   ├── test/
│   └── ...
├── code/             # Pasta para código fonte (se houver)
│   ├── data_processing.py
│   ├── model.py
│   └── ...
└── requirements.txt  # Arquivo com as dependências do Python
```

## Autor e Licença

Este projeto foi desenvolvido como parte do artigo de TCC.

Licença: [Se aplicável, mencione a licença]