from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from mongoengine.errors import NotUniqueError
from .models import User, Cart, Order,Review, OrderedProduct
from mongoengine.errors import DoesNotExist, ValidationError
import logging
import razorpay
from django.conf import settings
from vendor.models import Product
from vendor.serializers import ProductSerializer
from .serializers import UserSerializer, CartSerializer, OrderSerializer, ReviewSerializer
from .authentication import get_tokens_for_user, MongoJWTAuthentication
from bson import ObjectId
logger = logging.getLogger(__name__)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if not password or password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User(
                username=data.get('username'),
                email=data.get('email'),
                usertype=data.get('usertype')
            )
            user.set_password(password)  # Hash the password
            user.save()

            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)

        except NotUniqueError:
            return Response({'error': 'Username or Email already exists'}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Find user in MongoDB
        user = User.objects(email=email).first()
        
        if not user or not user.check_password(password):
            return Response({'error': 'Incorrect email or password'}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = get_tokens_for_user(user)

        serializer = UserSerializer(user)  # Serialize user details

        return Response({
            'user': serializer.data,
            'refresh': tokens['refresh'],
            'access': tokens['access'],
        }, status=status.HTTP_200_OK)

class CartView(APIView):
    """Handles adding to cart and fetching cart items"""
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve all cart items for the authenticated user"""
        try:
            cart_items = Cart.objects.filter(user=request.user)
            serializer = CartSerializer(cart_items, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching cart: {str(e)}")
            return Response({"error": "Failed to fetch cart items"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Add a product to the cart"""
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Check if the product is already in the cart
            cart_item = Cart.objects(user=request.user, product=product).first()
            if cart_item:
                cart_item.quantity += 1  # Increment quantity if it already exists
            else:
                cart_item = Cart(user=request.user, product=product, quantity=1)

            cart_item.save()
            serializer = CartSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as ve:
            logger.error(f"Validation error: {str(ve)}")
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({"error": "Failed to add product to cart"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """Remove a product from the cart"""
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(user=request.user, product=product_id)
            cart_item.delete()
            return Response({"message": "Product removed from cart"}, status=status.HTTP_200_OK)
        except DoesNotExist:
            return Response({"error": "Product not found in cart"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": "Failed to remove product"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class OrderView(APIView):
    """Handles creating an order from the cart"""
    
    permission_classes = [IsAuthenticated]
    authentication_classes = [MongoJWTAuthentication]
    
    def post(self, request):
        """Create an order from the user's cart"""
        try:
            # Fetch user's cart items
            user_cart = Cart.objects(user=request.user)
            if not user_cart:
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

            ordered_products = []
            product_serializer = ProductSerializer()

            for item in user_cart:
                product = item.product
                image_urls = product_serializer.get_image_urls(product)  # Get image URLs correctly

                ordered_products.append(
                    OrderedProduct(
                        product_id=str(product.id),
                        name=product.name,
                        price=product.price,
                        quantity=item.quantity,
                        image_url=image_urls[0] if image_urls else ""  # Use image URLs safely
                    )
                )


            # Create new order without cart_items
            order = Order(
                user=request.user,
                ordered_products=ordered_products,
                total_price=sum(item.product.price * item.quantity for item in user_cart),
                vendor=user_cart.first().product.vendor  # Assuming products have a vendor field
            )
            order.save()

            # Clear cart after order
            user_cart.delete()

            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return Response({"error": "Failed to create order"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def debug_mongo_references(request):
        """Debug helper to diagnose MongoDB reference issues"""
        from bson import ObjectId
        
        user = request.user
        logger.debug("=== MongoDB Debug Information ===")
        logger.debug(f"User object: {user}")
        logger.debug(f"User type: {type(user)}")
        logger.debug(f"User ID: {user.id}")
        logger.debug(f"User ID type: {type(user.id)}")
        
        # Check if the user ID is valid for MongoDB
        try:
            if isinstance(user.id, str):
                obj_id = ObjectId(user.id)
                logger.debug(f"Converted to ObjectId: {obj_id}")
            else:
                logger.debug("User ID is not a string, might be an ObjectId already")
        except Exception as e:
            logger.debug(f"Failed to convert to ObjectId: {e}")
        
        # Try to fetch a sample order
        try:
            sample_order = Order.objects.first()
            if sample_order:
                logger.debug(f"Sample order: {sample_order}")
                logger.debug(f"Sample order user: {sample_order.user}")
                logger.debug(f"Sample order user type: {type(sample_order.user)}")
                logger.debug(f"Sample order user ID: {sample_order.user.id}")
        except Exception as e:
            logger.debug(f"Failed to fetch sample order: {e}")
        
        logger.debug("=== End Debug Information ===")
    def get(self, request):
        try:
            # Add explicit authentication_classes to make sure we're using MongoJWTAuthentication
            logger.debug(f"User ID type: {type(request.user.id)}")
            logger.debug(f"User ID: {request.user.id}")
            
            # In MongoEngine, we need to make sure we're querying correctly
            # Let's use the raw ID string to query
            user_id = str(request.user.id)
            orders = Order.objects(user=request.user)
            
            # Ensure we're properly serializing the order objects
            serialized_orders = OrderSerializer(orders, many=True).data
            return Response(serialized_orders, status=status.HTTP_200_OK)
            
        except AttributeError as e:
            logger.error(f"User attribute error: {e}")
            # Try a different approach - get the user ID directly if possible
            try:
                if hasattr(request.user, 'id'):
                    user_id = str(request.user.id)
                    # Try to fetch the actual user document first
                    user_doc = User.objects.get(id=user_id)
                    orders = Order.objects(user=user_doc)
                    return Response(OrderSerializer(orders, many=True).data, status=status.HTTP_200_OK)
            except Exception as nested_e:
                logger.error(f"Failed alternative approach: {nested_e}")
            
            return Response({"error": "Invalid user object"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VendorOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get the vendor's user ID
            vendor = request.user

            # Get all orders where the vendor's products are part of the order
            orders = Order.objects.filter(vendor=vendor)
            
            # Serialize orders and return the response
            serialized_orders = OrderSerializer(orders, many=True)
            return Response(serialized_orders.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class CreatePaymentView(APIView):
    """Create a payment order in Razorpay"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get the latest order for the user
            order = Order.objects.filter(user=request.user, status="Pending").first()
            if not order:
                return Response({"error": "No pending order found"}, status=status.HTTP_400_BAD_REQUEST)

            amount = int(order.total_price * 100)  # Convert amount to paise (INR)
            payment_order = razorpay_client.order.create({
                "amount": amount,
                "currency": "INR",
                "payment_capture": "1"
            })

            return Response({"order_id": payment_order["id"]}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating payment order: {str(e)}")
            return Response({"error": "Failed to create payment order"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyPaymentView(APIView):
    """Verify Razorpay payment and update order status"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            payment_id = request.data.get("razorpay_payment_id")
            order_id = request.data.get("razorpay_order_id")
            signature = request.data.get("razorpay_signature")

            if not payment_id or not order_id or not signature:
                return Response({"error": "Missing payment details"}, status=status.HTTP_400_BAD_REQUEST)

            # Verify payment signature
            params_dict = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }

            try:
                razorpay_client.utility.verify_payment_signature(params_dict)
            except razorpay.errors.SignatureVerificationError:
                return Response({"error": "Invalid payment signature"}, status=status.HTTP_400_BAD_REQUEST)

            # Update order status
            order = Order.objects.filter(user=request.user, status="Pending").first()
            if order:
                order.status = "Paid"
                order.save()

            return Response({"message": "Payment successful"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Payment verification failed: {str(e)}")
            return Response({"error": "Payment verification failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        """Add a review for a product"""
        try:
            product = Product.objects.get(id=product_id)
            review = Review(
                user=request.user,
                product=product,
                rating=request.data.get('rating'),
                review_text=request.data.get('review_text', "")
            )
            review.save()
            return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, product_id=None):
        """Fetch reviews for a product"""
        try:
            if product_id:
                reviews = Review.objects.filter(product=product_id)
            else:
                reviews = Review.objects.filter(user=request.user)

            return Response(ReviewSerializer(reviews, many=True).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateOrderStatusView(APIView):
    """View to update the order status"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [MongoJWTAuthentication]

    def patch(self, request, order_id):
        try:
            from bson import ObjectId
            
            # Convert string ID to ObjectId for MongoDB
            order = Order.objects.get(id=ObjectId(order_id))
            
            # Debug information
            print(f"Order vendor ID: {order.vendor.id}")
            print(f"Request user ID: {request.user.id}")

            # Check if the request user is the vendor of this order
            if str(request.user.id) != str(order.vendor.id):
                return Response({"error": "Permission denied - you are not the vendor for this order"}, 
                                status=status.HTTP_403_FORBIDDEN)

            new_status = request.data.get("status")
            if not new_status or new_status not in ["Pending", "Paid", "Shipped", "Delivered", "Cancelled"]:
                return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

            order.status = new_status
            order.save()

            return Response({
                "message": "Order status updated successfully", 
                "order": {
                    "id": str(order.id),
                    "status": order.status
                }
            }, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            print(traceback.format_exc())  # Print full traceback for debugging
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


