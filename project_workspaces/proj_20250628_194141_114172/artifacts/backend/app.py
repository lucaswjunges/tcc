from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# Initialize Flask app
def create_app():
    app = Flask(__name__)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
db = SQLAlchemy()
db.init_app(app)
mma = Marshmallow(app)

    # Product model
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(200))
    price = db.Column(db.Float)
    category = db.Column(db.String(50))
    stock = db.Column(db.Integer)
    
    def __init__(self, name, description, price, category, stock):
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.stock = stock
    
    def __repr__(self):
        return f'<Product {self.name}>'

    # Create database tables
db.create_all()

    # Product Schema for serialization
class ProductSchema(mma.ModelSchema):
        class Meta:
            model = Product
            fields = ('id', 'name', 'description', 'price', 'category', 'stock')

    # Routes
    @app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    schema = ProductSchema(many=True)
    return jsonify(schema.dump(products))

    @app.route('/api/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get(id)
    if not product:
        return {'error': 'Product not found'}, 404
    schema = ProductSchema()
    return jsonify(schema.dump(product))

    @app.route('/api/products', methods=['POST'])
def create_product():
    schema = ProductSchema()
    errors = schema.validate(request.json)
    if errors:
        return {'error': errors}, 400
    product = Product(**schema.load(request.json))
db.session.add(product)
db.session.commit()
return jsonify(schema.dump(product)), 201

    @app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get(id)
    if not product:
        return {'error': 'Product not found'}, 404
    schema = ProductSchema()
    errors = schema.validate(request.json, partial=True)
    if errors:
        return {'error': errors}, 400
    for key, value in schema.load(request.json, partial=True).items():
        setattr(product, key, value)
db.session.commit()
return jsonify(schema.dump(product))

    @app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get(id)
    if not product:
        return {'error': 'Product not found'}, 404
db.session.delete(product)
db.session.commit()
return '', 204

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)