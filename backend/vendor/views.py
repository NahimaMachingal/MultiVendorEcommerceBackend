#vendor/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Product
from bson import ObjectId
from django.http import HttpResponse, Http404
from .serializers import ProductSerializer
from mongoengine.errors import DoesNotExist, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
import logging
from bson.errors import InvalidId
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
class ProductListView(APIView):
    """Handles GET (all products) & POST (create product)"""

    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        try:
            products = Product.objects()
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def post(self, request):
        """Create a new product (only for vendors)."""
        if not hasattr(request, 'user') or not request.user or getattr(request.user, 'usertype', '') != "vendor":
            return Response({'error': 'Only vendors can add products'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Get product data from request
            product_data = request.data.dict() if hasattr(request.data, 'dict') else request.data.copy()
            
            # Handle multiple image files
            if 'images' in request.FILES:
                product_data['images'] = request.FILES.getlist('images')
            
            serializer = ProductSerializer(data=product_data, context={'request': request})
            if serializer.is_valid():
                try:
                    product = serializer.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except ValidationError as ve:
                    logger.error(f"MongoEngine validation error: {str(ve)}")
                    return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    logger.error(f"Error saving product: {str(e)}")
                    return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in product creation: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductDetailView(APIView):
    """Handles GET, PUT, DELETE for a single product"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self, product_id):
        try:
            return Product.objects.get(id=ObjectId(product_id))
        except (Product.DoesNotExist, InvalidId):
            raise Http404("Product not found")

    def get(self, request, product_id):
        """Retrieve a single product by ID."""
        product = self.get_object(product_id)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, product_id):
        """Update product details (only for vendor who owns it)."""
        product = self.get_object(product_id)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(request, 'user') or not request.user or str(product.vendor.id) != str(request.user.id):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        # Get data from request
        product_data = request.data.dict() if hasattr(request.data, 'dict') else request.data.copy()
        
        # Handle image files
        if 'images' in request.FILES:
            product_data['images'] = request.FILES.getlist('images')

        serializer = ProductSerializer(product, data=product_data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error updating product: {str(e)}")
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id):
        """Delete a product (only for the vendor who owns it)."""
        product = self.get_object(product_id)
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(request, 'user') or not request.user or str(product.vendor.id) != str(request.user.id):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        try:
            product.delete()
            return Response({'message': 'Product deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting product: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Add a view to serve images
class ProductImageView(APIView):
    def get(self, request, product_id, image_index):
        try:
            # Get the product by ID
            product = Product.objects.get(id=product_id)
            
            # Check if the requested image index exists
            if not product.images or image_index >= len(product.images):
                raise Http404("Image not found")
            
            # Get the image from GridFS
            image = product.images[image_index]
            
            # Create a response with the image data
            response = HttpResponse(image.read(), content_type=image.content_type)
            response['Content-Disposition'] = f'inline; filename="{image.filename}"'
            return response
            
        except DoesNotExist:
            raise Http404("Product not found")
        except Exception as e:
            logger.error(f"Error serving image: {str(e)}")
            return HttpResponse(str(e), status=500)

class ProductPerformanceUpdateView(APIView):
    """
    View for updating product performance data (for development/testing purposes).
    This would normally come from actual order data in a production environment.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Get all products for the current vendor
        vendor = request.user
        products = Product.objects.filter(vendor=vendor)
        
        if not products:
            return Response({"message": "No products found for this vendor"}, status=status.HTTP_404_NOT_FOUND)
        
        updated_products = []
        
        for product in products:
            # Generate realistic sales data if not present
            if product.sales_count == 0:
                # Random sales between 5 and 50
                sales = random.randint(5, 50)
                # Calculate revenue based on price and sales
                revenue = round(product.price * sales, 2)
                
                # Update the product
                product.sales_count = sales
                product.revenue = revenue
                product.save()
                
                updated_products.append({
                    "id": str(product.id),
                    "name": product.name,
                    "sales_count": sales,
                    "revenue": revenue
                })
            else:
                updated_products.append({
                    "id": str(product.id),
                    "name": product.name,
                    "sales_count": product.sales_count,
                    "revenue": product.revenue
                })
        
        return Response({
            "message": "Product performance data updated successfully",
            "updated_products": updated_products
        }, status=status.HTTP_200_OK)

class VendorProductsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        vendor = request.user
        products = Product.objects.filter(vendor=vendor)
        
        # If products exist but have no sales data, generate some example data
        for product in products:
            if product.sales_count == 0:
                # Random sales between 5 and 50
                sales = random.randint(5, 50)
                # Calculate revenue based on price and sales
                revenue = round(product.price * sales, 2)
                
                # Update the product with sample data
                product.sales_count = sales
                product.revenue = revenue
                product.save()
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class VendorProducts(APIView):

    def get(self, request):
        try:
            if not request.user.is_authenticated:
                return Response({'error': 'User not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Fetch products only for the logged-in vendor
            products = Product.objects(vendor=request.user)

            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)