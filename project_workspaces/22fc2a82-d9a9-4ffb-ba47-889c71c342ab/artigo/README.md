# Artigo IEEE: Sistema de Prevenção de Falhas em Motores Industriais usando Visão Computacional, CNN e Machine Learning

## Descrição do Projeto

Este artigo apresenta um sistema inovador para a prevenção de falhas em motores industriais utilizando técnicas de visão computacional, redes neurais convolucionais (CNN) e aprendizado de máquina. O sistema foi desenvolvido para monitorar em tempo real as condições de operação dos motores, detectando sinais precoces de falhas e alertando os operadores antes que ocorram interrupções ou danos significativos.

## Objetivo Geral

O principal objetivo deste trabalho é propor e validar um modelo de detecção de falhas em motores industriais baseado em análise visual de vibrações e anomalias mecânicas, utilizando visão computacional para extração de características e CNN para classificação. O sistema busca reduzir custos operacionais e aumentar a segurança industrial por meio da previsão de falhas.

## Metodologia

### Coleta de Dados
- Captura de imagens térmicas e visuais de motores em operação normal e com falhas simuladas
- Anotação manual de anomalias e condições de falha
- Coleta de dados de sensores complementares (vibração, temperatura, etc.)

### Pré-processamento
- Normalização das imagens
- Aumento de dados através de rotações, cortes e adição de ruído
- Extração de características via transformada de Hough e análise de bordas

### Modelo CNN