# customer/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import User  # Import your MongoEngine User model
from rest_framework import exceptions

class MongoJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Attempt to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token['user_id']
            
            # Find user by string ID in MongoDB
            user = User.objects.get(id=user_id)

            # Add Django-style authentication properties
            user.is_authenticated = True
            
            return user
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')

from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user):
    user_id = str(user.id)  # Convert MongoDB ObjectId to string
    
    refresh = RefreshToken()
    refresh['user_id'] = user_id

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }