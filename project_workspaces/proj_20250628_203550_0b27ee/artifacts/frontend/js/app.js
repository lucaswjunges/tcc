(() => {
    // Variáveis globais
    const cart = [];
    const filters = {
        type: 'all',
        range: 'all',
        status: 'all',
    };
    const searchQuery = '';

    // Elementos do DOM
    const cartItemsContainer = document.getElementById('cart-items');
    const filtersContainer = document.getElementById('filters');
    const searchInput = document.getElementById('search-input');
    const cartBadge = document.getElementById('cart-badge');
    const productsContainer = document.getElementById('products');

    // Inicialização
    document.addEventListener('DOMContentLoaded', () => {
        loadProducts();
        setupEventListeners();
        updateCart();
    });

    function setupEventListeners() {
        // Adicionar ao carrinho
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('add-to-cart')) {
                const productId = e.target.dataset.id;
                addToCart(productId);
            }
        });

        // Filtrar produtos
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('filter-btn')) {
                applyFilters();
            }
        });

        // Pesquisar produtos
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value;
            loadProducts();
        });

        // Navegação por páginas
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('pagination-btn')) {
                e.preventDefault();
                const page = e.target.dataset.page;
                loadProducts(page);
            }
        });
    }

    function loadProducts(page = 1) {
        // Simulando chamada à API
        const apiUrl = `https://api.example.com/products?page=${page}&search=${searchQuery}&filters=${JSON.stringify(filters)}`;
        
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro na API');
                }
                return response.json();
            })
            .then(data => {
                renderProducts(data);
            })
            .catch(error => {
                console.error('Erro ao carregar produtos:', error);
                // Exibir mensagem para o usuário
                productsContainer.innerHTML = '<p class="error-message">Erro ao carregar produtos. Tente novamente mais tarde.</p>';
            });
    }

    function renderProducts(products) {
        productsContainer.innerHTML = '';
        
        if (products.length === 0) {
            productsContainer.innerHTML = '<p>Nenhum produto encontrado.</p>';
            return;
        }
        
        products.forEach(product => {
            const productCard = document.createElement('div');
            productCard.className = 'product-card';
            productCard.innerHTML = `
                <img src="${product.image}" alt="${product.name}">
                <h3>${product.name}</h3>
                <p>Preço: ${product.price}</p>
                <button class="add-to-cart" data-id="${product.id}">Adicionar ao Carrinho</button>
            `;
            productsContainer.appendChild(productCard);
        });
    }

    function addToCart(productId) {
        const existingItem = cart.find(item => item.id === productId);
        
        if (existingItem) {
            existingItem.quantity++;
        } else {
            cart.push({
                id: productId,
                name: '', // Seria preenchido com dados do produto
                price: 0, // Seria preenchido com dados do produto
                quantity: 1
            });
        }
        
        updateCart();
        showNotification('Produto adicionado ao carrinho!');
    }

    function updateCart() {
        // Atualizar o badge do carrinho
        cartBadge.textContent = cart.reduce((total, item) => total + item.quantity, 0);
        
        // Atualizar o conteúdo do carrinho
        if (cart.length === 0) {
            cartItemsContainer.innerHTML = '<p>Seu carrinho está vazio.</p>';
            return;
        }
        
        let total = 0;
        cartItemsContainer.innerHTML = cart.map(item => {
            const itemTotal = item.price * item.quantity;
            total += itemTotal;
            return `<div class="cart-item">
                <p>${item.name} - R$ ${item.price.toFixed(2)}</p>
                <p>Quantidade: ${item.quantity}</p>
                <p>Total: R$ ${itemTotal.toFixed(2)}</p>
            </div>`;
        }).join('');
        
        cartItemsContainer.innerHTML += `<p>Total: R$ ${total.toFixed(2)}</p>`;
    }

    function applyFilters() {
        // Lógica para aplicar filtros
        // Esta seria a seção onde você implementaria a lógica de filtro
        // com base nos botões selecionados
        loadProducts();
    }

    function showNotification(message) {
        // Criar elemento de notificação
        const notification = document.createElement('div');
        notification.textContent = message;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.backgroundColor = '#4CAF50';
        notification.style.color = 'white';
        notification.style.padding = '10px';
        notification.style.borderRadius = '5px';
        notification.style.zIndex = '1000';
        notification.style.boxShadow = '0 3px 5px rgba(0,0,0,0.2)';
        
        document.body.appendChild(notification);
        
        // Remover após 3 segundos
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 500);
        }, 3000);
    }

    // Exportar funções para uso em outros módulos se necessário
    window.loadProducts = loadProducts;
    window.updateCart = updateCart;
    window.addToCart = addToCart;
    window.showNotification = showNotification;
    window.applyFilters = applyFilters;
})();
