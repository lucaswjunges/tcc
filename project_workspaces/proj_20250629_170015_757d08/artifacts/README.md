# Sistema de Prevenção de Falhas em Motores Industriais

Este repositório contém o código e a documentação para um sistema de prevenção de falhas em motores industriais utilizando técnicas de **Redes Neurais Convolucionais (CNN)** e **Visão Computacional**. O sistema analisa imagens de motores em operação para detectar sinais precoces de falhas, auxiliando na manutenção preditiva e aumento da eficiência operacional.

## Objetivo

Desenvolver um sistema que:
- Capture e processe imagens de motores em operação
- Utilize CNNs para identificar padrões associados a falhas
- Gerar alertas em tempo real para prevenir falhas catastróficas

## Pré-requisitos

### Ambiente de Desenvolvimento
- Python 3.8+
- PyTorch 1.12+
- CUDA Toolkit (se disponível)
- OpenCV
- NumPy
- Pandas
- Matplotlib
- scikit-learn

### Configuração do Ambiente
1. Crie um ambiente virtual:
   ```bash
   python -m venv env
   source env/bin/activate
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Estrutura do Projeto
```
├── Sistema_Prevencao_Falhas_Motores/             # Pasta principal
│   ├── dados/                                 # Dados de treinamento e teste
│   │   ├── imagens/                           # Conjuntos de dados
│   │   │   ├── treino/                        # Dados de treinamento
│   │   │   └── teste/                         # Dados de teste
│   │   └── labels.csv                         # Anotações
│   ├── modelos/                               # Arquivos de modelo treinado
│   │   └── modelo_cnn.pth                      # Modelo treinado
│   ├── resultados/                            # Outputs do sistema
│   │   ├── logs/                             # Logs de execução
│   │   └── predicoes/                        # Arquivos de predição
│   ├── src/                                  # Código fonte
│   │   ├── captura.py                        # Captura de imagem em tempo real
│   │   ├── processamento.py                  # Processamento de imagem
│   │   ├── cnn_model.py                      # Implementação da CNN
│   │   ├── treinamento.py                    # Script de treinamento
│   │   └── interface.py                      # Interface de usuário
│   ├── docs/                                  # Documentação
│   │   ├── README.md                         # Documentação do projeto
│   │   └── artigo.tex                        # Estrutura do artigo LaTeX
│   └── requirements.txt                      # Dependências do projeto

## Instalação
### Dependências
Assegure-se de que todas as bibliotecas listadas nos requisitos estão instaladas.

### Configuração do Dataset
1. Baixe os dados de imagens de motores em operação
2. Organize os dados nas pastas `treino` e `teste`
3. Crie o arquivo `labels.csv` com a estrutura:
   ```
   caminho/imagem.jpg,classe(0 para funcionamento normal, 1 para falha)
   ```

## Execução
### 1. Treinamento do Modelo
```bash
to Treinar o modelo, execute o script `treinamento.py`:
python src/treinamento.py

O script realizará o seguinte:
- Carregar os dados de treinamento
- Definir a arquitetura da CNN
- Configurar o treinamento com early stopping
- Salvar o melhor modelo em `modelos/modelo_cnn.pth`
```

### 2. Teste do Modelo
```bash
Para testar o modelo, execute:
python src/processamento.py

Isso realizará:
- Carregar o modelo treinado
- Processar imagens de teste
- Gerar relatório de desempenho (acurácia, matriz de confusão, etc.)
```

## Uso do Sistema em Tempo Real
1. Execute o script de captura de imagens:
   ```bash
   python src/captura.py
   ```
2. O sistema capturará imagens do motor em tempo real
3. As imagens serão processadas pela CNN
4. Resultados serão exibidos na interface

## Exemplo de Saída
### Imagem Capturada
![Exemplo de imagem capturada](docs/imagens_exemplo.jpg)

### Gráfico de Acurácia
![Gráfico de Acurácia](docs/accuracy_plot.png)

### Matriz de Confusão
![Matriz de Confusão](docs/confusion_matrix.png)

## Contribuição
Este projeto foi desenvolvido para fins acadêmicos e de demonstração. Qualquer contribuição é bem-vinda.

## Licença
MIT License

## Referências
[1] "Deep Learning for Industrial Motor Fault Diagnosis" - Journal of Engineering Applications
[2] "Computer Vision Techniques for Motor Monitoring" - IEEE Transactions on Industrial Informatics

---

Este README foi gerado automaticamente. Para mais detalhes, consulte a documentação completa no diretório `docs`.