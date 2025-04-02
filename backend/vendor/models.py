
#vendor/models.py
from mongoengine import Document, StringField, ReferenceField, FloatField, IntField, ListField, DateTimeField, BooleanField, FileField
from datetime import datetime
from mongoengine import Document, StringField, ListField, FileField

class Product(Document):
    vendor = ReferenceField('User', required=True)
    name = StringField(required=True, max_length=255, unique=True)
    description = StringField()
    price = FloatField(required=True, min_value=0)
    stock = IntField(required=True, default=0)
    category = StringField(required=True)
    images = ListField(FileField())  # Use FileField directly in the ListField
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    is_active = BooleanField(default=True)
    sales_count = IntField(default=0)  # Track how many times the product is sold
    revenue = FloatField(default=0) 

    meta = {
        'indexes': [
            {'fields': ['name'], 'unique': True},  # Explicitly define the index to match existing one
            {'fields': ['category']},
            {'fields': ['vendor']}
        ]
    }
    def save(self, *args, **kwargs):
        """Manually update `updated_at` field before saving."""
        self.updated_at = datetime.utcnow()
        return super(Product, self).save(*args, **kwargs)