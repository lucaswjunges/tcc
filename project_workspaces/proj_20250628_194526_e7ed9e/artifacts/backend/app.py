from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory database for products
products = [
    {"id": 1, "name": "Product 1", "description": "Description 1", "price": 19.99},
    {"id": 2, "name": "Product 2", "description": "Description 2", "price": 29.99}
]

# Helper function to find product by ID
def find_product(product_id):
    for product in products:
        if product["id"] == product_id:
            return product
    return None

# Route to get all products
@app.route('/products', methods=['GET'])
def get_products():
    return jsonify(products)

# Route to get a single product
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = find_product(product_id)
    if product:
        return jsonify(product)
    else:
        return jsonify({"error": "Product not found"}), 404

# Route to create a new product
@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    if not data or 'name' not in data or 'price' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    # Generate a new ID
    new_id = max(p["id"] for p in products) + 1 if products else 1
    new_product = {
        "id": new_id,
        "name": data['name'],
        "description": data.get('description', ''),
        "price": data['price']
    }
    products.append(new_product)
    return jsonify(new_product), 201

# Route to update a product
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = find_product(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    data = request.get_json()
    if data:
        product.update(data)  # Updates only the keys present in data
    return jsonify(product)

# Route to delete a product
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = find_product(product_id)
    if product:
        products = [p for p in products if p['id'] != product_id]
        return jsonify({"result": True})
    else:
        return jsonify({"error": "Product not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)