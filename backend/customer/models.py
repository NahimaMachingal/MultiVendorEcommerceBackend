from mongoengine import Document, ListField,StringField, EmailField, ReferenceField,ObjectIdField, IntField, DateTimeField, FloatField
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from vendor.models import Product
from mongoengine import EmbeddedDocument, EmbeddedDocumentField

class User(Document):
    username = StringField(required=True, unique=True, min_length=3, max_length=50)
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)  # Store only hashed password
    usertype = StringField(choices=["customer", "admin","vendor",], required=True)
    
    def set_password(self, raw_password):
        """Hashes and sets the password."""
        self.password = generate_password_hash(raw_password)
    
    def check_password(self, raw_password):
        """Verifies the hashed password."""
        return check_password_hash(self.password, raw_password)

    meta = {'collection': 'users'}  # Optional: specify collection name

class Cart(Document):
    user = ReferenceField('User', required=True)
    product = ReferenceField('Product', required=True)
    quantity = IntField(required=True, min_value=1, default=1)
    added_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            {'fields': ['user']},  
            {'fields': ['product']}
        ]
    }
class OrderedProduct(EmbeddedDocument):
    product_id = ObjectIdField(required=True)
    name = StringField(required=True)
    price = FloatField(required=True)
    quantity = IntField(required=True)
    image_url = StringField()

class Order(Document):
    """Model to store order details"""
    user = ReferenceField(User, required=True)
    ordered_products = ListField(EmbeddedDocumentField(OrderedProduct))
    total_price = FloatField(required=True, min_value=0)
    status = StringField(choices=["Pending", "Paid", "Shipped", "Delivered", "Cancelled"], default="Pending")
    ordered_at = DateTimeField(default=datetime.utcnow)
    vendor = ReferenceField('User', required=True)
    meta = {
        'indexes': [
            {'fields': ['user']},  
            {'fields': ['status']},
            {'fields': ['vendor']}
        ]
    }
    def update_product_sales(self):
        """Update product sales count and revenue when an order is placed"""
        for ordered_product in self.ordered_products:
            product = Product.objects(id=ordered_product.product_id).first()
            if product:
                product.sales_count += ordered_product.quantity
                product.revenue += ordered_product.price * ordered_product.quantity
                product.save()

    def calculate_total_price(self):
        """Calculate total price based on ordered products"""
        self.total_price = sum(item.price * item.quantity for item in self.ordered_products)
        self.save()

class Review(Document):
    user = ReferenceField('User', required=True)  # User who writes the review
    product = ReferenceField('Product', required=True)  # Product being reviewed
    rating = IntField(required=True, min_value=1, max_value=5)  # Rating (1-5)
    review_text = StringField()  # Optional review text
    created_at = DateTimeField(default=datetime.utcnow)  # Timestamp

    meta = {
        'indexes': [
            {'fields': ['product']},  
            {'fields': ['user']}
        ]
    }
