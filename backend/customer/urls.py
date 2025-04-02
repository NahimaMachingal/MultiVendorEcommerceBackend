from django.urls import path
from . import views
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView

urlpatterns = [
    path('api/token/',TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path("cart/", CartView.as_view(), name="cart"),
    path("orders/", OrderView.as_view(), name="orders"),
    path("payments/create/", CreatePaymentView.as_view(), name="create_payment"),
    path("payments/verify/", VerifyPaymentView.as_view(), name="verify_payment"),
    path('reviews/<str:product_id>/', ReviewView.as_view(), name='reviews'),  # Fetch or create reviews for a product
    path('my-reviews/', ReviewView.as_view(), name='my-reviews'),  # Fetch reviews by user
    path('orders/vendor/', views.VendorOrderView.as_view(), name='vendor-orders'),
    path("orders/<str:order_id>/update-status/", UpdateOrderStatusView.as_view(), name="update-order-status"),
    
]