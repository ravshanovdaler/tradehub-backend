"""
email_utils.py — Centralised HTML email helpers for UzB2B Wholesale.

Covers:
  • send_registration_otp  – new account e-mail verification
  • send_resend_otp        – resend OTP for pending registration
  • send_password_reset    – password-reset verification code
"""

from django.core.mail import send_mail
from django.conf import settings


# ─────────────────────────────────────────────
#  Shared design tokens
# ─────────────────────────────────────────────
_BRAND_COLOR    = "#4F46E5"   # Indigo-600 — primary brand
_BRAND_DARK     = "#3730A3"   # Indigo-800
_ACCENT_COLOR   = "#06B6D4"   # Cyan-500
_BG_OUTER       = "#0F0F1A"   # Near-black canvas
_BG_CARD        = "#1A1A2E"   # Deep navy card
_BG_OTP         = "#12122A"   # OTP box background
_TEXT_PRIMARY   = "#F0F0FF"   # Almost white
_TEXT_MUTED     = "#94A3B8"   # Slate-400
_TEXT_ACCENT    = "#818CF8"   # Indigo-400
_BORDER_COLOR   = "#2D2D5E"   # Subtle border
_FONT_STACK     = "Inter, 'Helvetica Neue', Arial, sans-serif"


def _base_html(title: str, preheader: str, body_content: str) -> str:
    """
    Wraps body_content in a full responsive HTML email shell.
    Compatible with Gmail, Outlook, Apple Mail, and most mobile clients.
    """
    return f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <title>{title}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body, html {{ margin: 0; padding: 0; background: {_BG_OUTER}; }}
    body {{ -webkit-font-smoothing: antialiased; }}
    a {{ text-decoration: none; }}
    .email-body {{ background: {_BG_OUTER}; padding: 40px 20px; }}
    .card {{ background: {_BG_CARD}; border-radius: 20px; max-width: 560px; margin: 0 auto;
              border: 1px solid {_BORDER_COLOR}; overflow: hidden; }}
    .header {{ background: linear-gradient(135deg, {_BRAND_COLOR} 0%, {_ACCENT_COLOR} 100%);
               padding: 36px 40px 32px; text-align: center; }}
    .logo-text {{ font-family: {_FONT_STACK}; font-size: 22px; font-weight: 800;
                  color: #FFFFFF; letter-spacing: -0.3px; }}
    .logo-text span {{ color: rgba(255,255,255,0.7); font-weight: 500; }}
    .body {{ padding: 36px 40px; }}
    .greeting {{ font-family: {_FONT_STACK}; font-size: 24px; font-weight: 700;
                 color: {_TEXT_PRIMARY}; margin-bottom: 14px; line-height: 1.3; }}
    .message {{ font-family: {_FONT_STACK}; font-size: 15px; color: {_TEXT_MUTED};
                line-height: 1.7; margin-bottom: 32px; }}
    .otp-wrapper {{ text-align: center; margin: 0 0 32px; }}
    .otp-label {{ font-family: {_FONT_STACK}; font-size: 11px; font-weight: 600;
                  color: {_TEXT_ACCENT}; letter-spacing: 2px; text-transform: uppercase;
                  margin-bottom: 14px; display: block; }}
    .otp-box {{ display: inline-block; background: {_BG_OTP}; border: 2px solid {_BRAND_COLOR};
                border-radius: 16px; padding: 24px 48px; }}
    .otp-digits {{ font-family: 'Courier New', 'Lucida Console', monospace;
                   font-size: 42px; font-weight: 700; letter-spacing: 14px;
                   color: #FFFFFF; }}
    .otp-timer {{ font-family: {_FONT_STACK}; font-size: 13px; color: {_TEXT_MUTED};
                  margin-top: 14px; display: block; }}
    .otp-timer strong {{ color: #F87171; }}
    .info-box {{ background: rgba(79,70,229,0.08); border-left: 3px solid {_BRAND_COLOR};
                 border-radius: 0 10px 10px 0; padding: 16px 20px; margin-bottom: 28px; }}
    .info-box p {{ font-family: {_FONT_STACK}; font-size: 13.5px; color: {_TEXT_MUTED}; line-height: 1.6; }}
    .info-box p strong {{ color: {_TEXT_PRIMARY}; }}
    .divider {{ border: none; border-top: 1px solid {_BORDER_COLOR}; margin: 28px 0; }}
    .footer {{ padding: 0 40px 32px; text-align: center; }}
    .footer p {{ font-family: {_FONT_STACK}; font-size: 12px; color: {_TEXT_MUTED};
                 line-height: 1.7; margin-bottom: 6px; }}
    .footer a {{ color: {_TEXT_ACCENT}; }}
    .footer .brand-line {{ font-size: 13px; color: {_TEXT_PRIMARY}; font-weight: 600; margin-bottom: 8px; }}
    .bottom-line {{ height: 4px; background: linear-gradient(90deg, {_BRAND_COLOR}, {_ACCENT_COLOR}, {_BRAND_COLOR}); }}
    @media only screen and (max-width: 580px) {{
      .header {{ padding: 28px 24px; }}
      .body, .footer {{ padding-left: 24px; padding-right: 24px; }}
      .otp-digits {{ font-size: 34px; letter-spacing: 10px; }}
      .otp-box {{ padding: 20px 32px; }}
    }}
  </style>
</head>
<body>
  <div style="display:none;font-size:1px;color:{_BG_OUTER};line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
    {preheader}
  </div>
  <table class="email-body" width="100%" cellpadding="0" cellspacing="0" role="presentation">
    <tr><td>
      <div class="card">
        <div class="header">
          <div class="logo-text">&#x1F3EA; UzB2B <span>Wholesale</span></div>
        </div>
        <div class="body">
          {body_content}
        </div>
        <hr class="divider" />
        <div class="footer">
          <p class="brand-line">UzB2B Wholesale Marketplace</p>
          <p>You received this email because an action was performed on your account.<br/>
             If you did not initiate this, please ignore this email or <a href="mailto:support@uzb2b.com">contact support</a>.</p>
          <p style="margin-top:14px;">&#169; 2026 UzB2B Wholesale. All rights reserved.</p>
        </div>
        <div class="bottom-line"></div>
      </div>
    </td></tr>
  </table>
</body>
</html>"""


def _otp_block(otp: str, validity_minutes: int = 10) -> str:
    """Returns the styled OTP display block HTML."""
    return f"""
    <div class="otp-wrapper">
      <span class="otp-label">Your Verification Code</span>
      <div class="otp-box">
        <div class="otp-digits">{otp}</div>
      </div>
      <span class="otp-timer">
        This code expires in <strong>{validity_minutes} minutes</strong>. Do not share it with anyone.
      </span>
    </div>
    """


# ─────────────────────────────────────────────
#  1.  Registration / email-verification OTP
# ─────────────────────────────────────────────
def send_registration_otp(email: str, otp: str, first_name: str = "") -> None:
    """Send beautiful HTML email verification OTP after registration."""
    name_greeting = f"Hi {first_name}," if first_name else "Welcome!"

    body = f"""
    <h2 class="greeting">&#x1F389; {name_greeting}</h2>
    <p class="message">
      Thank you for joining <strong style="color:{_TEXT_PRIMARY}">UzB2B Wholesale Marketplace</strong>!
      You are one step away from accessing Uzbekistan's leading B2B trading platform.
      <br/><br/>
      Please enter the verification code below to confirm your email address and activate your account.
    </p>
    {_otp_block(otp)}
    <div class="info-box">
      <p>
        <strong>Why do we verify emails?</strong><br/>
        Verifying your email keeps your account secure and ensures you receive important
        order updates, seller notifications, and platform alerts.
      </p>
    </div>
    """

    html_message = _base_html(
        title="Verify Your Email — UzB2B Wholesale",
        preheader=f"Your UzB2B verification code is {otp}. Enter it to activate your account.",
        body_content=body,
    )

    plain_message = (
        f"Hello {first_name or 'there'},\n\n"
        f"Welcome to UzB2B Wholesale Marketplace!\n\n"
        f"Your email verification code is: {otp}\n\n"
        f"This code expires in 10 minutes. Do not share it with anyone.\n\n"
        f"Best regards,\nUzB2B Team"
    )

    send_mail(
        subject="Verify your email — UzB2B Wholesale",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=True,
    )


# ─────────────────────────────────────────────
#  2.  Resend OTP (pending registration)
# ─────────────────────────────────────────────
def send_resend_otp(email: str, otp: str) -> None:
    """Send a new OTP when the user requests a resend during registration."""

    body = f"""
    <h2 class="greeting">&#x1F504; New Verification Code</h2>
    <p class="message">
      You requested a new verification code for your
      <strong style="color:{_TEXT_PRIMARY}">UzB2B Wholesale</strong> account.
      <br/><br/>
      Use the code below to verify your email address and complete your registration.
    </p>
    {_otp_block(otp)}
    <div class="info-box">
      <p>
        <strong>Did not request a new code?</strong><br/>
        If you did not ask for a new verification code, your previous code is still valid.
        You can safely ignore this email.
      </p>
    </div>
    """

    html_message = _base_html(
        title="New Verification Code — UzB2B Wholesale",
        preheader=f"Your new UzB2B verification code is {otp}. It expires in 10 minutes.",
        body_content=body,
    )

    plain_message = (
        f"Hello,\n\n"
        f"You requested a new verification code for your UzB2B account.\n\n"
        f"Your new verification code is: {otp}\n\n"
        f"This code expires in 10 minutes. Do not share it with anyone.\n\n"
        f"Best regards,\nUzB2B Team"
    )

    send_mail(
        subject="Your new verification code — UzB2B Wholesale",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=True,
    )


# ─────────────────────────────────────────────
#  3.  Password reset OTP
# ─────────────────────────────────────────────
def send_password_reset_otp(email: str, otp: str, first_name: str = "") -> None:
    """Send password-reset verification code."""
    name_greeting = f"Hi {first_name}," if first_name else "Hello,"

    body = f"""
    <h2 class="greeting">&#x1F510; {name_greeting}</h2>
    <p class="message">
      We received a request to reset the password for your
      <strong style="color:{_TEXT_PRIMARY}">UzB2B Wholesale</strong> account
      associated with <strong style="color:{_TEXT_ACCENT}">{email}</strong>.
      <br/><br/>
      Enter the code below in the app to create a new password.
    </p>
    {_otp_block(otp)}
    <div class="info-box">
      <p>
        <strong>&#x26A0;&#xFE0F; Didn't request a password reset?</strong><br/>
        If you did not make this request, your account may be at risk.
        Please <a href="mailto:support@uzb2b.com" style="color:{_TEXT_ACCENT};">contact our support team</a>
        immediately so we can help secure your account.
      </p>
    </div>
    """

    html_message = _base_html(
        title="Reset Your Password — UzB2B Wholesale",
        preheader=f"Your UzB2B password reset code is {otp}. It expires in 10 minutes.",
        body_content=body,
    )

    plain_message = (
        f"Hello {first_name or 'there'},\n\n"
        f"You requested a password reset for your UzB2B account.\n\n"
        f"Your verification code is: {otp}\n\n"
        f"This code expires in 10 minutes. Do not share it with anyone.\n\n"
        f"If you did not request this, please contact support immediately.\n\n"
        f"Best regards,\nUzB2B Team"
    )

    send_mail(
        subject="Reset your password — UzB2B Wholesale",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=True,
    )
