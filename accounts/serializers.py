from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SellerProfile, BuyerProfile, Report

User = get_user_model()


class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = [
            'company_name', 'business_address', 'address_latitude',
            'address_longitude', 'registration_number', 'doc_file',
            'is_verified', 'verification_notes', 'quick_replies',
            'company_description', 'company_logo', 'order_approve_message_template'
        ]

        read_only_fields = ['is_verified', 'verification_notes']


class BuyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerProfile
        fields = [
            'delivery_address', 'delivery_latitude', 'delivery_longitude',
            'passport_image', 'order_message_template', 'quick_replies'
        ]


class UserSerializer(serializers.ModelSerializer):
    seller_profile = SellerProfileSerializer(required=False)
    buyer_profile = BuyerProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'additional_phone', 'age',
            'is_seller', 'is_buyer', 'email_verified', 'currency', 'language',
            'seller_profile', 'buyer_profile'
        ]
        read_only_fields = ['id', 'email_verified']

    def update(self, instance, validated_data):
        seller_profile_data = validated_data.pop('seller_profile', None)
        buyer_profile_data = validated_data.pop('buyer_profile', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if instance.is_seller and seller_profile_data:
            profile, _ = SellerProfile.objects.get_or_create(user=instance)
            for attr, value in seller_profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        if instance.is_buyer and buyer_profile_data:
            profile, _ = BuyerProfile.objects.get_or_create(user=instance)
            for attr, value in buyer_profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match."})
        return data



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    # Privacy & Policy agreement — must be True to register
    agreed_to_privacy_policy = serializers.BooleanField(required=True)

    # Seller-specific fields
    company_name = serializers.CharField(required=False, allow_blank=True)
    business_address = serializers.CharField(required=False, allow_blank=True)
    address_latitude = serializers.FloatField(required=False, allow_null=True)
    address_longitude = serializers.FloatField(required=False, allow_null=True)
    registration_number = serializers.CharField(required=False, allow_blank=True)

    # Buyer-specific fields
    delivery_address = serializers.CharField(required=False, allow_blank=True)
    delivery_latitude = serializers.FloatField(required=False, allow_null=True)
    delivery_longitude = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone_number', 'additional_phone', 'age',
            'is_seller', 'is_buyer', 'currency',
            'agreed_to_privacy_policy',
            # Seller
            'company_name', 'business_address', 'address_latitude', 'address_longitude',
            'registration_number',
            # Buyer
            'delivery_address', 'delivery_latitude', 'delivery_longitude',
        ]

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        age = data.get('age')
        if age is not None and age < 18:
            raise serializers.ValidationError({'age': 'You must be at least 18 years old to register.'})
        if not data.get('is_seller') and not data.get('is_buyer'):
            raise serializers.ValidationError({'role': 'Please select a role: Buyer or Seller.'})
        phone = data.get('phone_number')
        if phone and User.objects.filter(phone_number=phone).exists():
            raise serializers.ValidationError({'phone_number': 'A user with this phone number already exists.'})
        # Enforce privacy policy agreement
        if not data.get('agreed_to_privacy_policy'):
            raise serializers.ValidationError(
                {'agreed_to_privacy_policy': 'You must agree to the Privacy Policy and Terms of Service to register.'}
            )
        # Round coordinates to 6dp so the model DecimalField never rejects them
        for coord_field in ('address_latitude', 'address_longitude', 'delivery_latitude', 'delivery_longitude'):
            val = data.get(coord_field)
            if val is not None:
                data[coord_field] = round(float(val), 6)
        return data

    def create(self, validated_data):
        is_seller = validated_data.get('is_seller', False)
        is_buyer = validated_data.get('is_buyer', False)

        # Pop extra fields
        validated_data.pop('confirm_password', None)
        company_name = validated_data.pop('company_name', '')
        business_address = validated_data.pop('business_address', '')
        address_latitude = validated_data.pop('address_latitude', None)
        address_longitude = validated_data.pop('address_longitude', None)
        registration_number = validated_data.pop('registration_number', '')
        delivery_address = validated_data.pop('delivery_address', '')
        delivery_latitude = validated_data.pop('delivery_latitude', None)
        delivery_longitude = validated_data.pop('delivery_longitude', None)

        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        # Generate OTP for email verification
        from .models import generate_otp
        user.email_otp = generate_otp()
        user.email_verified = False
        user.save()

        if is_seller:
            SellerProfile.objects.create(
                user=user,
                company_name=company_name,
                business_address=business_address,
                address_latitude=address_latitude,
                address_longitude=address_longitude,
                registration_number=registration_number
            )

        if is_buyer:
            BuyerProfile.objects.create(
                user=user,
                delivery_address=delivery_address,
                delivery_latitude=delivery_latitude,
                delivery_longitude=delivery_longitude,
            )

        return user



class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match."})
        return data


class SupportMessageSerializer(serializers.Serializer):
    """Serializer for user → support team messages sent to admin Gmail."""
    title = serializers.CharField(required=True, max_length=200)
    message = serializers.CharField(required=True)
    # Optional file attachment (image/video/document)
    media = serializers.FileField(required=False, allow_null=True)


class ReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.ReadOnlyField(source='reporter.username')

    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reporter_username', 'report_type', 
            'reported_user', 'reported_product', 'reported_chat', 
            'reason', 'description', 'created_at', 'is_resolved'
        ]
        read_only_fields = ['id', 'reporter', 'created_at', 'is_resolved']

