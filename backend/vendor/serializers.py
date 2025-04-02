#vendor/serializers.py
# vendor/serializers.py
from rest_framework import serializers
from .models import Product
from customer.models import User
from datetime import datetime
from bson import ObjectId
import base64
import uuid

class ProductSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()  
    name = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    price = serializers.FloatField(required=True, min_value=0)
    stock = serializers.IntegerField(required=True, min_value=0)
    category = serializers.CharField(required=True)
    images = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)
    image_urls = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(default=True)
    sales_count = serializers.IntegerField(read_only=True)  # Track number of times sold
    revenue = serializers.FloatField(read_only=True)
    
    def get_id(self, obj):
        return str(obj.id)
    
    def get_vendor(self, obj):
        return obj.vendor.username if obj.vendor else None
    
    def get_image_urls(self, obj):
        """Return URLs for images if they exist"""
        if not obj.images:
            return []
        # For GridFS files, you would construct URLs to access them
        return [f"/api/products/image/{str(obj.id)}/{i}" for i in range(len(obj.images))]

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError({"error": "Authentication required"})

        if request.user.usertype != "vendor":
            raise serializers.ValidationError({"error": "Only vendors can add products"})

        # Extract and handle image files separately
        image_files = validated_data.pop('images', [])
        
        # Store the actual User object reference
        validated_data["vendor"] = request.user
        
        # Create product without images first
        product = Product(**validated_data)
        
        # Now handle each image file and save them to GridFS
        if image_files:
            for image_file in image_files:
                # Use MongoEngine's FileField functionality directly
                # This requires reading the file content
                content = image_file.read()
                
                # Create a new GridFSProxy object
                from mongoengine.fields import GridFSProxy
                from mongoengine import get_db
                
                # Get the GridFS from MongoEngine's connection
                grid_fs = GridFSProxy()
                
                # Set the content and metadata
                filename = image_file.name
                content_type = image_file.content_type or 'application/octet-stream'
                
                # Store directly through MongoEngine's mechanism
                grid_fs.put(content, filename=filename, content_type=content_type)
                
                # Add to product images
                product.images.append(grid_fs)
        
        product.save()
        return product
    def update(self, instance, validated_data):
        image_files = validated_data.pop('images', None)
        if image_files:
            print(f"Processing {len(image_files)} new images")
            # Instead of clearing all images, you could append
            # Or keep the clear if that's the intended behavior
            instance.images = []
            
            for image_file in image_files:
                try:
                    # Debug the image file
                    print(f"Processing image: {image_file.name}, size: {image_file.size}")
                    
                    content = image_file.read()
                    from mongoengine.fields import GridFSProxy
                    
                    grid_fs = GridFSProxy()
                    grid_fs.put(content, filename=image_file.name, 
                            content_type=image_file.content_type or 'application/octet-stream')
                    
                    instance.images.append(grid_fs)
                    print("Image successfully added to instance")
                except Exception as e:
                    print(f"Error processing image: {str(e)}")
        
        # Update other fields and save
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.updated_at = datetime.utcnow()
        try:
            instance.save()
            print("Product successfully saved with images")
        except Exception as e:
            print(f"Error saving product: {str(e)}")
        return instance