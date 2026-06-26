from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils import timezone
from .serializers import (
    RegisterSerializer, UserSerializer, SellerProfileSerializer, BuyerProfileSerializer,
    PasswordChangeSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    SupportMessageSerializer
)
from .models import SellerProfile, BuyerProfile, generate_otp, PendingUser

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

User = get_user_model()



class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        email = data['email']
        
        if User.objects.filter(email=email).exists():
            return Response({'email': ['A user with this email already exists.']}, status=status.HTTP_400_BAD_REQUEST)
            
        from decimal import Decimal
        data_to_store = dict(data)
        data_to_store['password'] = make_password(data['password'])
        for key, val in list(data_to_store.items()):
            if isinstance(val, Decimal):
                data_to_store[key] = float(val)
        
        otp = generate_otp()
        
        PendingUser.objects.update_or_create(
            email=email,
            defaults={
                'otp': otp,
                'registration_data': data_to_store
            }
        )
        
        try:
            send_mail(
                subject='Verify your email - UzB2B Wholesale',
                message=f"Hello,\n\nWelcome to UzB2B Wholesale Marketplace!\n\nYour email verification code is: {otp}\n\nBest regards,\nUzB2B Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass
            
        res_data = {'message': 'Verification code sent to your email.'}
        if settings.DEBUG:
            res_data['otp'] = otp
            
        return Response(res_data, status=status.HTTP_200_OK)



class VerifyEmailView(APIView):
    """Verify email via OTP sent after registration, then create active user profile."""
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({'error': 'Email and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pending = PendingUser.objects.get(email=email)
        except PendingUser.DoesNotExist:
            return Response({'error': 'No pending registration found for this email.'}, status=status.HTTP_404_NOT_FOUND)

        if pending.otp != otp:
            return Response({'error': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)

        data = pending.registration_data
        
        # Create active user account
        user = User.objects.create(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data['phone_number'],
            additional_phone=data.get('additional_phone'),
            age=data.get('age'),
            is_seller=data['is_seller'],
            is_buyer=data['is_buyer'],
            email_verified=True
        )

        if user.is_seller:
            SellerProfile.objects.create(
                user=user,
                company_name=data.get('company_name', ''),
                business_address=data.get('business_address', ''),
                address_latitude=data.get('address_latitude'),
                address_longitude=data.get('address_longitude'),
                registration_number=data.get('registration_number', '')
            )
        elif user.is_buyer:
            BuyerProfile.objects.create(
                user=user,
                delivery_address=data.get('delivery_address', ''),
                delivery_latitude=data.get('delivery_latitude'),
                delivery_longitude=data.get('delivery_longitude'),
            )

        # Remove the temporary registration record
        pending.delete()

        # Generate token
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'message': 'Email verified and account created successfully!',
            'token': token.key,
            'user': _build_user_payload(user)
        }, status=status.HTTP_201_CREATED)


class ResendOTPView(APIView):
    """Resend OTP to pending user email."""
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pending = PendingUser.objects.get(email=email)
        except PendingUser.DoesNotExist:
            return Response({'error': 'No pending registration found for this email.'}, status=status.HTTP_404_NOT_FOUND)

        otp = generate_otp()
        pending.otp = otp
        pending.save()

        try:
            send_mail(
                subject='Your new verification code - UzB2B',
                message=f"Hello,\n\nYour new verification code is: {otp}\n\nBest regards,\nUzB2B Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass

        res_data = {'message': 'A new verification code has been sent to your email.'}
        if settings.DEBUG:
            res_data['otp'] = otp
        return Response(res_data, status=status.HTTP_200_OK)



def _build_user_payload(user):
    """Helper to build a consistent user payload for login/verify responses."""
    company_name = ""
    is_verified = False
    delivery_address = ""
    seller_profile = None
    if user.is_seller and hasattr(user, 'seller_profile'):
        company_name = user.seller_profile.company_name
        is_verified = user.seller_profile.is_verified
        seller_profile = {
            'company_name': company_name,
            'is_verified': is_verified,
            'registration_number': user.seller_profile.registration_number,
            'business_address': user.seller_profile.business_address,
            'quick_replies': user.seller_profile.quick_replies,
            'company_description': user.seller_profile.company_description,
            'company_logo': user.seller_profile.company_logo.url if user.seller_profile.company_logo else None,
            'order_approve_message_template': user.seller_profile.order_approve_message_template,
        }


    buyer_profile = None
    if user.is_buyer and hasattr(user, 'buyer_profile'):
        delivery_address = user.buyer_profile.delivery_address
        buyer_profile = {
            'delivery_address': delivery_address,
            'order_message_template': user.buyer_profile.order_message_template,
            'quick_replies': user.buyer_profile.quick_replies,
        }

    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.phone_number,
        'is_seller': user.is_seller,
        'is_buyer': user.is_buyer,
        'email_verified': user.email_verified,
        'company_name': company_name,
        'is_verified': is_verified,
        'delivery_address': delivery_address,
        'seller_profile': seller_profile,
        'buyer_profile': buyer_profile,
    }


class LoginView(APIView):
    """
    Login with username, email, or phone number + password.
    Accepts: { "identifier": "...", "password": "..." }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        identifier = request.data.get('identifier') or request.data.get('username')
        password = request.data.get('password')

        if not identifier or not password:
            return Response(
                {'error': 'Please provide identifier (username/email/phone) and password.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Try to resolve user by username, email, or phone
        user_obj = None
        # By username
        user_obj = User.objects.filter(username=identifier).first()
        # By email
        if not user_obj:
            user_obj = User.objects.filter(email=identifier).first()
        # By phone number
        if not user_obj:
            user_obj = User.objects.filter(phone_number=identifier).first()

        if not user_obj:
            return Response({'error': 'No account found with this identifier.'}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate using the resolved username
        user = authenticate(username=user_obj.username, password=password)
        if not user:
            return Response({'error': 'Invalid password.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.deletion_requested:
            return Response({'error': 'This account is pending deletion approval by administration.'}, status=status.HTTP_403_FORBIDDEN)

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': _build_user_payload(user)
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user


class CompanyLogoUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_seller:
            return Response(
                {'error': 'Only sellers can upload a company logo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            profile = user.seller_profile
        except SellerProfile.DoesNotExist:
            profile = SellerProfile.objects.create(user=user)

        logo_file = request.FILES.get('company_logo')
        if not logo_file:
            return Response({'error': 'No company logo file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        profile.company_logo = logo_file
        profile.save()

        return Response({
            'message': 'Company logo uploaded successfully.',
            'company_logo': profile.company_logo.url,
            'user': _build_user_payload(user)
        }, status=status.HTTP_200_OK)


class SellerDocumentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_seller:
            return Response(
                {'error': 'Only sellers can upload verification documents.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            profile = user.seller_profile
        except SellerProfile.DoesNotExist:
            profile = SellerProfile.objects.create(user=user)

        serializer = SellerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BuyerPassportUploadView(APIView):
    """Upload buyer passport document."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_buyer:
            return Response(
                {'error': 'Only buyers can upload passport documents.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            profile = user.buyer_profile
        except BuyerProfile.DoesNotExist:
            profile = BuyerProfile.objects.create(user=user)

        serializer = BuyerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        if not user.check_password(old_password):
            return Response({'old_password': ['Incorrect old password.']}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        # Delete old token and generate a new one so the user stays logged in
        Token.objects.filter(user=user).delete()
        new_token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'message': 'Password changed successfully.',
            'token': new_token.key
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {'error': 'No account found with this email address. Please enter the email you registered with.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp = generate_otp()
        user.email_otp = otp
        user.save()

        try:
            send_mail(
                subject='Reset your password - UzB2B Wholesale',
                message=f"Hello,\n\nYou requested a password reset. Your verification code is: {otp}\n\nBest regards,\nUzB2B Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass

        res_data = {'message': 'Password reset verification code sent to your email.'}
        if settings.DEBUG:
            res_data['otp'] = otp

        return Response(res_data, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        user = User.objects.filter(email=email).first()
        if not user or user.email_otp != otp:
            return Response({'otp': ['Invalid email or verification code.']}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.email_otp = None
        user.save()

        return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)


class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.is_buyer:
            user.delete()
            return Response({'message': 'Your account has been deleted successfully.'}, status=status.HTTP_200_OK)
        elif user.is_seller:
            user.deletion_requested = True
            user.deletion_requested_at = timezone.now()
            user.save()
            return Response({'message': 'Deletion request submitted for administrator review.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Unsupported user role.'}, status=status.HTTP_400_BAD_REQUEST)


class SupportMessageView(APIView):
    """Authenticated users can send a support message to the admin email.
    The email includes: username, email, title, message, and optional media attachment."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    SUPPORT_EMAIL = 'ravshanovdaler06@gmail.com'

    def post(self, request, *args, **kwargs):
        serializer = SupportMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        title = serializer.validated_data['title']
        message_body = serializer.validated_data['message']
        media_file = request.FILES.get('media')

        # Build the email body
        email_body = (
            f"Support Request from UzB2B User\n"
            f"{'=' * 50}\n\n"
            f"Username   : {user.username}\n"
            f"Email      : {user.email}\n"
            f"Full Name  : {user.get_full_name()}\n"
            f"Role       : {'Seller' if user.is_seller else 'Buyer'}\n\n"
            f"Title      : {title}\n"
            f"{'─' * 40}\n"
            f"{message_body}\n"
        )

        try:
            email = EmailMessage(
                subject=f"[UzB2B Support] {title}",
                body=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[self.SUPPORT_EMAIL],
                reply_to=[user.email],
            )

            # Attach media file if provided
            if media_file:
                email.attach(media_file.name, media_file.read(), media_file.content_type)

            email.send(fail_silently=False)
        except Exception as e:
            return Response(
                {'error': f'Failed to send support message: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {'message': 'Your support message has been sent successfully. We will get back to you soon.'},
            status=status.HTTP_200_OK
        )


class CompanyProfileView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, seller_id, *args, **kwargs):
        try:
            seller = User.objects.get(id=seller_id, is_seller=True)
            profile = seller.seller_profile
        except (User.DoesNotExist, SellerProfile.DoesNotExist):
            return Response({'error': 'Company not found.'}, status=status.HTTP_404_NOT_FOUND)

        from orders.models import Order
        orders_made = Order.objects.filter(seller=seller).exclude(status__in=['PENDING', 'CANCELLED']).count()

        from .models import CompanyLike
        likes_count = CompanyLike.objects.filter(company=profile).count()

        is_liked_by_user = False
        if request.user and request.user.is_authenticated:
            is_liked_by_user = CompanyLike.objects.filter(user=request.user, company=profile).exists()

        from products.models import Product
        from products.serializers import ProductSerializer
        products_queryset = Product.objects.filter(seller=seller).prefetch_related('images', 'variants', 'reviews').order_by('-created_at')
        products_serializer = ProductSerializer(products_queryset, many=True, context={'request': request})

        payload = {
            'id': seller.id,
            'company_name': profile.company_name,
            'business_address': profile.business_address,
            'company_description': profile.company_description,
            'company_logo': profile.company_logo.url if profile.company_logo else None,
            'is_verified': profile.is_verified,
            'orders_made': orders_made,
            'likes_count': likes_count,
            'is_liked_by_user': is_liked_by_user,
            'products': products_serializer.data
        }
        return Response(payload, status=status.HTTP_200_OK)


class CompanyLikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, seller_id, *args, **kwargs):
        try:
            seller = User.objects.get(id=seller_id, is_seller=True)
            profile = seller.seller_profile
        except (User.DoesNotExist, SellerProfile.DoesNotExist):
            return Response({'error': 'Company not found.'}, status=status.HTTP_404_NOT_FOUND)

        from .models import CompanyLike
        like_obj, created = CompanyLike.objects.get_or_create(user=request.user, company=profile)
        if not created:
            like_obj.delete()
            liked = False
        else:
            liked = True

        likes_count = CompanyLike.objects.filter(company=profile).count()
        return Response({
            'liked': liked,
            'likes_count': likes_count
        }, status=status.HTTP_200_OK)



