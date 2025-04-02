# Multi-Vendor E-Commerce Platform - Backend

This backend is built using Django REST Framework (DRF) with JWT authentication, MongoDB (MongoEngine) for data storage, and Razorpay for payment processing.

## Objective

Develop a robust Multi-Vendor E-Commerce Platform where:
- Vendors can manage products, view orders, and track performance
- Customers can browse, add to cart, and purchase products

## Features

### User Roles
- **Vendor**: Manages products (add, edit, delete), views order details, and tracks sales
- **Customer**: Browses products, adds to cart, applies coupons, and places orders

### Vendor Dashboard
- ✅ **Product Management**: CRUD operations for products (name, price, images, stock, category)
- ✅ **Order Management**: View order details related to their products
- ✅ **Analytics**: Track sales, revenue, and stock levels

### Customer Features
- ✔️ Browse products by category
- ✔️ Add to cart, remove from cart, and proceed to checkout
- ✔️ Apply discount codes and coupons
- ✔️ Track order history & status (Pending, Shipped, Delivered)

### Payment Integration
- 💳 Implemented a dummy payment flow
- 💰 Bonus: Integrated Razorpay for real transactions

### Backend & Database Integration
- 🔹 Stores users, products, orders, and cart data in MongoDB using MongoEngine
- 🔹 Implements caching using Redis for fast product retrieval
- 🔹 Ensures API security against SQL injection, XSS, and CSRF attacks

## Technical Stack

### Backend
- 🚀 Django REST Framework (DRF) for building RESTful APIs
- 🔐 JWT authentication for secure user login and access control
- 🛢 MongoDB (via MongoEngine) for efficient data storage
- ⚡ Redis for caching frequently accessed data
- 💳 Razorpay for handling online payments

### API Endpoints
- 🔹 User Authentication (JWT-based login & registration)
- 🔹 Product Management (CRUD operations for vendors)
- 🔹 Order Processing (Customer checkout & order tracking)
- 🔹 Cart Management (Add/remove items, apply discounts)
- 🔹 Admin Panel (optional, for managing vendors & customers)

## Getting Started

### Install Dependencies
```bash
pip install -r requirements.txt
Run Migrations & Start Server
bashCopypython manage.py migrate
python manage.py runserver
🔗 Open http://127.0.0.1:8000 to access the API.
Environment Variables
Create a .env file and configure the necessary variables:
CopySECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=mongodb://localhost:27017/your_db_name
JWT_SECRET=your_jwt_secret
RAZORPAY_KEY=your_razorpay_key
REDIS_URL=redis://localhost:6379/0
Deployment

🚀 Deploy on AWS, DigitalOcean, or Heroku
⚙️ Use Gunicorn & Nginx for production setup
🛢 Set up MongoDB Atlas for cloud database storage

Learn More

📖 Django REST Framework
📖 MongoEngine Documentation
📖 Razorpay API Docs
