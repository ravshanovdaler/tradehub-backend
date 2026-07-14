from django.urls import path
from .views import (
    RegisterView, LoginView, UserProfileView, CompanyLogoUploadView,
    SellerDocumentUploadView, KYCUploadView,
    VerifyEmailView, ResendOTPView,
    PasswordChangeView, PasswordResetRequestView, PasswordResetConfirmView,
    DeleteAccountView, SupportMessageView,
    CompanyProfileView, CompanyLikeToggleView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/upload-logo/', CompanyLogoUploadView.as_view(), name='upload_logo'),
    path('upload-doc/', SellerDocumentUploadView.as_view(), name='upload_doc'),
    path('upload-passport/', KYCUploadView.as_view(), name='upload_passport'),
    path('password-change/', PasswordChangeView.as_view(), name='password_change'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('support/', SupportMessageView.as_view(), name='support_message'),
    path('companies/<int:seller_id>/', CompanyProfileView.as_view(), name='company_profile'),
    path('companies/<int:seller_id>/like/', CompanyLikeToggleView.as_view(), name='company_like_toggle'),
]

