from rest_framework import serializers
from .models import User, Order  # Import the User model


class UserSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)  # MongoDB stores `_id` as a string
    username = serializers.CharField(max_length=50, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    usertype = serializers.ChoiceField(choices=["customer", "admin","vendor",], required=True)

    def create(self, validated_data):
        """Create a new user with hashed password."""
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
            usertype=validated_data["usertype"]
        )
        user.set_password(validated_data["password"])  # Hash password
        user.save()
        return user

    def update(self, instance, validated_data):
        """Update user details."""
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.usertype = validated_data.get("usertype", instance.usertype)
        
        if "password" in validated_data:
            instance.set_password(validated_data["password"])  # Hash new password
        
        instance.save()
        return instance

from rest_framework import serializers
from .models import Cart
from vendor.serializers import ProductSerializer

class CartSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    product = ProductSerializer(read_only=True)
    quantity = serializers.IntegerField()
    added_at = serializers.DateTimeField()

    def get_id(self, obj):
        return str(obj.id)

    def get_user(self, obj):
        return obj.user.username if obj.user else None
class OrderedProductSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    name = serializers.CharField()
    price = serializers.FloatField()
    quantity = serializers.IntegerField()
    image_url = serializers.CharField(required=False, allow_blank=True)

class OrderSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    ordered_products = OrderedProductSerializer(many=True, read_only=True)
    total_price = serializers.FloatField()
    status = serializers.CharField()
    ordered_at = serializers.DateTimeField()

    def get_id(self, obj):
        return str(obj.id)

    def get_user(self, obj):
        # Handle possibly missing user reference
        try:
            if obj.user:
                return obj.user.username
        except Exception as e:
            # Log the error but don't break serialization
            logger.error(f"Error getting username: {e}")
            return None
        return None
    def get_vendor(self, obj):
        """Retrieve the vendor associated with the order"""
        return obj.vendor.username if obj.vendor else None

class ReviewSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    product = ProductSerializer(read_only=True)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    review_text = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField()

    def get_id(self, obj):
        return str(obj.id)

    def get_user(self, obj):
        return obj.user.username if obj.user else None

