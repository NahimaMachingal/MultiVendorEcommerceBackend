#vendor/urls.py
from django.urls import path
from .views import ProductListView, ProductDetailView, ProductImageView, VendorProductsView, ProductPerformanceUpdateView,VendorProducts 

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<str:product_id>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/image/<str:product_id>/<int:image_index>/', ProductImageView.as_view(), name='product-image'),
    path('products/vendor/products/', VendorProductsView.as_view(), name='vendor-product-list'),
    path('products/vendor/products/performance/update/', ProductPerformanceUpdateView.as_view(), name='product-performance-update'),
    path('products/vendors/products/', VendorProducts.as_view(), name='vendor-products'),
]
