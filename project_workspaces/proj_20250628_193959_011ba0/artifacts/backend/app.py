from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Product(BaseModel):
    id: int
    name: str
    brand: str
    price: float
    category: str

# Simulação de banco de dados em memória
products = [
    Product(id=1, name="Pod Caliburn", brand="Uwell", price=79.99, category="Pod"),
    Product(id=2, name="Vape Drag X", brand="Voopoo", price=199.99, category="Vape")
]

@app.get("/")
def read_root():
    return {"message": "Welcome to Vape Store API"}

@app.get("/products")
def list_products():
    return products

@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = next((p for p in products if p.id == product_id), None)
    return product if product else {"error": "Product not found"}
