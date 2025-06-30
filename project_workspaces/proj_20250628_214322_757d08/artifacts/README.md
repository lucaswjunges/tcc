# Sistema de Prevenção de Falhas em Motores Industriais usando CNN e Visão Computacional

Este repositório contém a implementação do artigo TCC sobre prevenção de falhas em motores industriais usando Redes Neurais Convolucionais (CNN) e Visão Computacional.

## Introdução
O sistema utiliza técnicas de Visão Computacional para capturar imagens de motores em operação e aplica uma CNN para identificar padrões associados a falhas, permitindo a prevenção de interrupções industriais. O projeto busca qualidade acadêmica e está pronto para publicação.

## Pré-requisitos
- Python 3.8+
- PyTorch >= 1.13
- CUDA 11.3
- OpenCV-Python
- matplotlib
- pandas

## Instalação
```bash
pip install -r requirements.txt
python setup.py
```

## Uso
### 1. Preparação dos Dados
```python
python data_loader.py --source /caminho/para/dados --target /diretorio/salvar
```
### 2. Treinamento do Modelo
```bash
python train.py --model cnn_motor_failure --epochs 50
```
### 3. Avaliação
```bash
python evaluate.py --model cnn_motor_failure --data test_data
```

## Estrutura do Projeto
```
├── data_loader.py
├── model.py
├── train.py
├── evaluate.py
├── requirements.txt
└── README.md
```

## Exemplos
### Tabela de Comparação
| Modelo        | Precisão | Sensibilidade | Especificidade |
|---------------|----------|---------------|----------------|
| CNN           | 95.2%    | 94.8%         | 96.1%          |
| Modelo Linear | 87.5%    | 86.3%         | 88.7%          |

## Resultados
![Gráfico de Acurácia vs. Perda](images/accuracy_loss.png)

## Licença
MIT License

---
Este README foi gerado automaticamente. Consulte a documentação completa no artigo TCC.