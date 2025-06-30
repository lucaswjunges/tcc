# VapeShop Website

Website completo para venda de produtos de vapes e pods, com design estiloso e funcionalidades avançadas.

## Índice
1. [Sobre](#sobre)
2. [Recursos](#recursos)
3. [Instalação](#instalação)
4. [Uso](#uso)
5. [Estrutura do Projeto](#estrutura-do-projeto)
6. [Exemplos](#exemplos)

## Sobre
Este projeto cria um website completo para venda de pods e vapes. O site inclui:
- Categorias de produtos
- Carrinho de compras
- Páginas de detalhes dos produtos
- Sistema de checkout
- Design responsivo e estiloso

## Recursos
- **Design Responsivo**: Funciona em dispositivos móveis e desktop
- **Catálogo de Produtos**: Exibição de produtos com imagens, descrições e preços
- **Filtração**: Produtos podem ser filtrados por categoria
- **Carrinho de Compras**: Adição e remoção de itens
- **Checkout**: Processo de finalização de compra
- **Base de Dados**: Armazenamento de produtos e pedidos

## Instalação
1. Clone o repositório
```bash
git clone https://github.com/seu_usuario/vapeshop.git
```

2. Instale as dependências
```bash
npm install
```

3. Configure a variável de ambiente `.env`
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=senha
DB_NAME=vapeshop
PORT=3000
```

4. Inicie o servidor
```bash
npm run dev
```

## Uso
- **Produtos**: Encontre produtos na página inicial ou na seção de produtos
- **Carrinho**: Adicione produtos ao carrinho e finalize a compra
- **Administração**: Acesse a página de administração para gerenciar produtos

## Estrutura do Projeto
```
/projeto
├── /public
│   ├── /css
│   └── /images
├── /src
│   ├── /components
│   ├── /pages
│   └── /services
├── /config
├── /models
├── /routes
└── package.json
```

## Exemplos
### Exemplo de produto
```json
{
  "id": 1,
  "name": "Pod Standard",
  "description": "Pod de 10ml com sabor a frutas",
  "price": 29.99,
  "category": "Pods",
  "image": "pod-standard.jpg"
}
```

### Exemplo de carrinho
```javascript
// Adicionar item ao carrinho
addToCart(productId, quantity) {
  // Lógica para adicionar ao carrinho
}

// Remover item do carrinho
removeFromCart(productId) {
  // Lógica para remover do carrinho
}
```

### Exemplo de checkout
```javascript
// Processo de checkout
checkout() {
  // Coleta dados do usuário
  // Processa pagamento
  // Confirmação de compra
}
```

Este README fornece uma visão geral completa do projeto e seus principais componentes.