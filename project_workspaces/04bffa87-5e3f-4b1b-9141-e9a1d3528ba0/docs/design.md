# Design do Website de Adivinhações de Tarô

## Descrição Geral
Site altamente estiloso para consultas de Tarô, completo e funcional, com sistema de pagamento e armazenamento de dados. O design deve ser sofisticado, mantendo a credibilidade e justiça do serviço.

## Páginas do Site

### 1. Página Inicial
- Header com logo e menu de navegação
- Seção hero com título impactante e chamada para ação
- Seção sobre os benefícios do serviço
- Galeria de depoimentos
- Seção de destaque para consultas populares
- Footer com informações de contato e links úteis

### 2. Página de Consulta
- Formulário para seleção do tipo de consulta
- Opções de personalização da consulta
- Calendário para seleção da data da consulta
- Botão para agendamento ou pagamento

### 3. Página de Resultados
- Exibição detalhada das cartas sorteadas
- Interpretação completa das cartas
- Análise detalhada da consulta
- Recomendações personalizadas

### 4. Página de Pagamento
- Opções de pagamento seguras
- Valores transparentes
- Processo de pagamento simplificado

### 5. Página de Informações
- Sobre o serviço
- Como funciona a leitura de Tarô
- Política de privacidade e dados
- Termos de serviço

## Design Visual

### Paleta de Cores
- Principal: #8B5A2B (marrom terroso)
- Secundário: #D4AF37 (dourado)
- Destaque: #F5F5DC (creme claro)
- Texto: #3E2723 (preto escuro)

### Tipografia
- Títulos: Playfair Display (serifa elegante)
- Texto: Lato (sans-serif moderno)

### Elementos Decorativos
- Ícones de Tarô (cartas, runas, pentagramas)
- Molduras de pergaminho
- Efeitos de luz sutis
- Gradientes sutis

## Banco de Dados

### Estrutura
- Tabela de Cartas (id, nome, significado_positivo, significado_negativo, imagem)
- Tabela de Clientes (id, nome, email, telefone, data_cadastro)
- Tabela de Consultas (id, cliente_id, data_consulta, tipo_consulta, valor_pago, status)
- Tabela de Resultados (id, consulta_id, carta_id, posição, interpretação)

## Backend

### run.py