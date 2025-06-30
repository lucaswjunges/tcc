// VapeShop Main JavaScript

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Main initialization function
function initializeApp() {
    initializeAnimations();
    initializeCartFunctionality();
    initializeSearch();
    initializeTooltips();
    initializeNavigation();
}

// Animation initialization
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    // Observe all cards and sections
    document.querySelectorAll('.card, section').forEach(el => {
        observer.observe(el);
    });
}

// Cart functionality
function initializeCartFunctionality() {
    // Initialize cart from localStorage
    let cart = getCart();
    updateCartUI();

    // Add to cart buttons
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            const productName = this.dataset.productName || 'Produto';
            const productPrice = parseFloat(this.dataset.productPrice) || 0;
            
            addToCart(productId, productName, productPrice);
            showCartNotification('Produto adicionado ao carrinho!');
            updateCartUI();
        });
    });

    // Remove from cart buttons
    document.querySelectorAll('.remove-from-cart').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            removeFromCart(productId);
            updateCartUI();
        });
    });
}

// Cart management functions
function getCart() {
    const cart = localStorage.getItem('vapeshop_cart');
    return cart ? JSON.parse(cart) : [];
}

function saveCart(cart) {
    localStorage.setItem('vapeshop_cart', JSON.stringify(cart));
}

function addToCart(productId, productName, productPrice, quantity = 1) {
    let cart = getCart();
    const existingItem = cart.find(item => item.id === productId);
    
    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({
            id: productId,
            name: productName,
            price: productPrice,
            quantity: quantity
        });
    }
    
    saveCart(cart);
}

function removeFromCart(productId) {
    let cart = getCart();
    cart = cart.filter(item => item.id !== productId);
    saveCart(cart);
}

function updateCartQuantity(productId, quantity) {
    let cart = getCart();
    const item = cart.find(item => item.id === productId);
    if (item) {
        item.quantity = Math.max(0, quantity);
        if (item.quantity === 0) {
            removeFromCart(productId);
        } else {
            saveCart(cart);
        }
    }
}

function getCartTotal() {
    const cart = getCart();
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
}

function getCartItemCount() {
    const cart = getCart();
    return cart.reduce((count, item) => count + item.quantity, 0);
}

// Update cart UI elements
function updateCartUI() {
    const cartBadges = document.querySelectorAll('.cart-badge');
    const cartCount = getCartItemCount();
    
    cartBadges.forEach(badge => {
        badge.textContent = cartCount;
        badge.style.display = cartCount > 0 ? 'inline' : 'none';
    });

    // Update cart total if on cart page
    const cartTotal = document.getElementById('cart-total');
    if (cartTotal) {
        cartTotal.textContent = `R$ ${getCartTotal().toFixed(2)}`;
    }
}

// Show cart notification
function showCartNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300);
        });
    }
}

function performSearch(query) {
    const products = document.querySelectorAll('.product-item');
    const searchTerm = query.toLowerCase();
    
    products.forEach(product => {
        const productName = product.dataset.name || '';
        const productCategory = product.dataset.category || '';
        const isVisible = productName.includes(searchTerm) || 
                         productCategory.includes(searchTerm);
        
        product.style.display = isVisible ? 'block' : 'none';
    });
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Navigation enhancements
function initializeNavigation() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Navbar background on scroll
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });
}

// Product filtering
function filterProductsByCategory(category) {
    const products = document.querySelectorAll('.product-item');
    
    products.forEach(product => {
        const productCategory = product.dataset.category;
        const shouldShow = category === 'all' || productCategory === category;
        
        if (shouldShow) {
            product.style.display = 'block';
            product.classList.remove('filtered-out');
        } else {
            product.style.display = 'none';
            product.classList.add('filtered-out');
        }
    });
}

// Product sorting
function sortProducts(sortBy) {
    const grid = document.getElementById('productsGrid');
    if (!grid) return;
    
    const products = Array.from(document.querySelectorAll('.product-item'));
    
    products.sort((a, b) => {
        switch(sortBy) {
            case 'name':
                return (a.dataset.name || '').localeCompare(b.dataset.name || '');
            case 'price_low':
                return parseFloat(a.dataset.price || 0) - parseFloat(b.dataset.price || 0);
            case 'price_high':
                return parseFloat(b.dataset.price || 0) - parseFloat(a.dataset.price || 0);
            case 'newest':
                return new Date(b.dataset.created || 0) - new Date(a.dataset.created || 0);
            default:
                return 0;
        }
    });
    
    products.forEach(product => grid.appendChild(product));
}

// Form validation
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Newsletter subscription
function subscribeNewsletter(email) {
    if (!validateEmail(email)) {
        showCartNotification('Por favor, insira um e-mail válido.', 'danger');
        return;
    }
    
    // Simulate API call
    showCartNotification('E-mail cadastrado com sucesso!', 'success');
    
    // Clear the input
    const emailInput = document.querySelector('input[type="email"]');
    if (emailInput) {
        emailInput.value = '';
    }
}

// Email validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Product quick view
function showProductQuickView(productId) {
    // This would typically fetch product data and show in a modal
    const modal = document.getElementById('quickViewModal');
    if (modal) {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}

// Wishlist functionality
function toggleWishlist(productId) {
    let wishlist = JSON.parse(localStorage.getItem('vapeshop_wishlist') || '[]');
    const index = wishlist.indexOf(productId);
    
    if (index > -1) {
        wishlist.splice(index, 1);
        showCartNotification('Produto removido da lista de desejos.', 'info');
    } else {
        wishlist.push(productId);
        showCartNotification('Produto adicionado à lista de desejos!', 'success');
    }
    
    localStorage.setItem('vapeshop_wishlist', JSON.stringify(wishlist));
    updateWishlistUI();
}

function updateWishlistUI() {
    const wishlist = JSON.parse(localStorage.getItem('vapeshop_wishlist') || '[]');
    
    document.querySelectorAll('.wishlist-btn').forEach(btn => {
        const productId = btn.dataset.productId;
        const isInWishlist = wishlist.includes(productId);
        
        btn.classList.toggle('active', isInWishlist);
        btn.querySelector('i').className = isInWishlist ? 'fas fa-heart' : 'far fa-heart';
    });
}

// Image lazy loading
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeLazyLoading();
    updateWishlistUI();
    
    // Newsletter form submission
    const newsletterForms = document.querySelectorAll('.newsletter-form');
    newsletterForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = this.querySelector('input[type="email"]').value;
            subscribeNewsletter(email);
        });
    });
});

// Export functions for global use
window.VapeShop = {
    addToCart,
    removeFromCart,
    updateCartQuantity,
    toggleWishlist,
    showProductQuickView,
    filterProductsByCategory,
    sortProducts,
    subscribeNewsletter
};