/*
 * app.js - Main JavaScript file for the vape shop website
 * Handles cart, filters, search, and API interactions
 */

// Cart functionality
const cart = {
  items: [],
  init() {
    this.loadCart();
    this.bindEvents();
  },
  loadCart() {
    const savedCart = localStorage.getItem('vapeShopCart');
    if (savedCart) {
      this.items = JSON.parse(savedCart);
    }
  },
  saveCart() {
    localStorage.setItem('vapeShopCart', JSON.stringify(this.items));
  },
  bindEvents() {
    document.querySelectorAll('.add-to-cart').forEach(button => {
      button.addEventListener('click', (e) => {
        const productId = e.target.dataset.productId;
        this.addItem(productId);
        this.saveCart();
        this.updateCartUI();
      });
    });
    
    document.querySelector('.remove-item')?.addEventListener('click', () => {
      this.removeItem();
      this.saveCart();
      this.updateCartUI();
    });
    
    document.querySelector('.update-quantity')?.addEventListener('click', () => {
      this.updateQuantity();
      this.saveCart();
      this.updateCartUI();
    });
    
    // Checkout button
    document.querySelector('.checkout-btn')?.addEventListener('click', () => {
      this.checkout();
    });
  },
  addItem(productId) {
    const existingItem = this.items.find(item => item.id === productId);
    
    if (existingItem) {
      existingItem.quantity += 1;
    } else {
      this.items.push({
        id: productId,
        name: '', // Will be populated later
        price: 0, // Will be populated later
        quantity: 1
      });
    }
  },
  removeItem(id) {
    this.items = this.items.filter(item => item.id !== id);
  },
  updateQuantity(id, change) {
    const item = this.items.find(item => item.id === id);
    if (item) {
      item.quantity += change;
      if (item.quantity <= 0) {
        this.removeItem(id);
      }
    }
  },
  checkout() {
    // In a real app, this would send cart data to the backend
    alert('Checkout functionality would be implemented here');
  },
  updateCartUI() {
    // Calculate totals
    const totalItems = this.items.reduce((sum, item) => sum + item.quantity, 0);
    const totalPrice = this.items.reduce(
      (sum, item) => sum + (item.price * item.quantity), 0
    );
    
    // Update UI elements
    document.getElementById('cart-count').textContent = totalItems;
    document.getElementById('cart-total').textContent = totalPrice.toFixed(2);
    
    // For demo purposes, we'll simulate fetching product details
    // In a real app, this would be done via API calls
    const cartList = document.getElementById('cart-items');
    cartList.innerHTML = '';
    
    this.items.forEach(item => {
      // Simulate API call to get product details
      setTimeout(() => {
        // This is where you'd normally fetch product details
        const productDetails = {
          name: `Vape Product ${item.id}`,
          price: (10 + item.id * 2).toFixed(2)
        };
        
        const cartItem = document.createElement('div');
        cartItem.className = 'cart-item';
        cartItem.dataset.id = item.id;
        cartItem.innerHTML = `
          <h4>${productDetails.name}</h4>
          <p>${productDetails.price} x ${item.quantity}</p>
          <button class="remove-item" data-id="${item.id}">Remove</button>
        `;
        cartList.appendChild(cartItem);
      }, 100 * this.items.indexOf(item));
    });
  }
};

// Product filters functionality
const filters = {
  activeFilters: {
    brand: [],
    category: [],
    priceRange: [0, 1000]
  },
  init() {
    this.bindEvents();
    this.applyFilters();
  },
  bindEvents() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const filterType = btn.dataset.filter;
        const filterValue = btn.dataset.value;
        
        if (btn.classList.contains('active')) {
          this.removeFilter(filterType, filterValue);
          btn.classList.remove('active');
        } else {
          this.addFilter(filterType, filterValue);
          btn.classList.add('active');
        }
        
        this.applyFilters();
      });
    });
    
    document.getElementById('price-range').addEventListener('input', (e) => {
      const range = e.target.value.split('-');
      this.setPriceRange(range[0], range[1]);
      this.applyFilters();
    });
  },
  addFilter(type, value) {
    if (!this.activeFilters[type].includes(value)) {
      this.activeFilters[type].push(value);
    }
  },
  removeFilter(type, value) {
    this.activeFilters[type] = this.activeFilters[type].filter(v => v !== value);
  },
  setPriceRange(min, max) {
    this.activeFilters.priceRange = [min, max];
  },
  applyFilters() {
    const products = document.querySelectorAll('.product');
    
    products.forEach(product => {
      const productBrand = product.dataset.brand;
      const productCategory = product.dataset.category;
      const productPrice = parseFloat(product.dataset.price);
      
      const brandFilter = this.activeFilters.brand.length === 0 || 
                         this.activeFilters.brand.includes(productBrand);
      
      const categoryFilter = this.activeFilters.category.length === 0 || 
                            this.activeFilters.category.includes(productCategory);
      
      const priceFilter = productPrice >= this.activeFilters.priceRange[0] && 
                         productPrice <= this.activeFilters.priceRange[1];
      
      if (brandFilter && categoryFilter && priceFilter) {
        product.style.display = 'block';
      } else {
        product.style.display = 'none';
      }
    });
  }
};

// Search functionality
const search = {
  query: '',
  init() {
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', (e) => {
      this.query = e.target.value.toLowerCase();
      this.performSearch();
    });
  },
  performSearch() {
    const products = document.querySelectorAll('.product');
    
    products.forEach(product => {
      const productName = product.querySelector('.product-name').textContent.toLowerCase();
      if (productName.includes(this.query)) {
        product.style.display = 'block';
      } else {
        product.style.display = 'none';
      }
    });
  }
};

// API interactions
const api = {
  async fetchProducts() {
    try {
      const response = await fetch('/api/products');
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching products:', error);
      return [];
    }
  },
  async fetchProductDetails(productId) {
    try {
      const response = await fetch(`/api/products/${productId}`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching product details:', error);
      return null;
    }
  }
};

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
  // Initialize core functionality
  cart.init();
  filters.init();
  search.init();
  
  // Load products from API on startup
  api.fetchProducts().then(products => {
    // This would be implemented to render products
  });
  
  // Initialize mock product UI for demo purposes
  const mockProducts = [
    { id: 1, name: 'Vape Device X', price: 29.99, brand: 'VapeTech', category: 'device' },
    { id: 2, name: 'Pod 2000', price: 19.99, brand: 'VapeTech', category: 'pod' },
    { id: 3, name: 'Flavor A', price: 5.99, brand: 'FlavorCo', category: 'e-liquid' },
    { id: 4, name: 'Flavor B', price: 6.99, brand: 'FlavorCo', category: 'e-liquid' },
  ];
  
  // Render products for demo purposes
  mockProducts.forEach(product => {
    const productElement = document.createElement('div');
    productElement.className = 'product';
    productElement.dataset.brand = product.brand;
    productElement.dataset.category = product.category;
    productElement.dataset.price = product.price;
    productElement.innerHTML = `
      <h3 class="product-name">${product.name}</h3>
      <p class="product-price">${product.price.toFixed(2)}</p>
      <button class="add-to-cart" data-product-id="${product.id}">Add to Cart</button>
    `;
    document.getElementById('product-list').appendChild(productElement);
  });
});