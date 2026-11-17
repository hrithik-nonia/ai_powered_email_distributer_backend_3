import logging
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

APP_NAME = os.getenv("APP_NAME", "InboxAI")
OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")
BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", APP_NAME)
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class EmailDeliveryError(Exception):
    pass


class EmailHelper:

    @classmethod
    async def send_otp_email(cls, recipient_email: str, otp: str) -> None:
        if not BREVO_API_KEY or not BREVO_SENDER_EMAIL:
            raise EmailDeliveryError("Brevo credentials not configured")

        payload = {
            "sender": {
                "name": BREVO_SENDER_NAME,
                "email": BREVO_SENDER_EMAIL,
            },
            "to": [{"email": recipient_email}],
            "subject": f"Your {APP_NAME} Verification Code",
            "htmlContent": cls._html_body(otp),
        }

        headers = {
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    BREVO_API_URL,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                logger.info("OTP email sent to %s via Brevo", recipient_email)

        except httpx.HTTPStatusError as exc:
            logger.error("Brevo error: %s", exc.response.text)
            raise EmailDeliveryError(f"Brevo rejected the request: {exc.response.status_code}")
        except httpx.RequestError as exc:
            logger.error("Brevo connection error: %s", exc)
            raise EmailDeliveryError("Could not connect to Brevo")

    @staticmethod
    def _html_body(otp: str) -> str:
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Verify Your Email</title>
</head>
<body style="margin:0;padding:0;background-color:#f0f4ff;
             font-family:'Segoe UI',Arial,sans-serif;color:#1f2937;">

  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#f0f4ff;padding:40px 16px;">
    <tr><td align="center">

      <!-- Card -->
      <table width="100%" cellpadding="0" cellspacing="0"
             style="max-width:520px;background:#ffffff;
                    border-radius:16px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);
                     padding:32px 40px;text-align:center;">
            <h1 style="margin:0;font-size:28px;font-weight:700;
                       color:#ffffff;letter-spacing:-0.5px;">
              📬 {APP_NAME}
            </h1>
            <p style="margin:8px 0 0;font-size:14px;color:#e0e7ff;">
              AI-powered email management
            </p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px;">

            <h2 style="margin:0 0 8px;font-size:22px;
                       font-weight:600;color:#111827;">
              Verify your email address
            </h2>
            <p style="margin:0 0 28px;font-size:15px;
                      line-height:1.6;color:#6b7280;">
              Use the code below to complete your registration.
              This code is valid for
              <strong style="color:#111827;">
                {OTP_EXPIRY_MINUTES} minutes
              </strong>.
            </p>

            <!-- OTP Box -->
            <div style="background:#f5f3ff;border:2px dashed #a5b4fc;
                        border-radius:12px;padding:24px;
                        text-align:center;margin-bottom:28px;">
              <p style="margin:0 0 8px;font-size:12px;
                        text-transform:uppercase;letter-spacing:2px;
                        color:#7c3aed;font-weight:600;">
                Your verification code
              </p>
              <span style="font-size:42px;font-weight:800;
                           letter-spacing:12px;color:#4f46e5;">
                {otp}
              </span>
            </div>

            <!-- Steps -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="margin-bottom:28px;">
              <tr>
                <td style="padding:12px;background:#f9fafb;
                           border-radius:8px;margin-bottom:8px;">
                  <p style="margin:0;font-size:14px;color:#374151;">
                    ✅ &nbsp;Enter this code on the verification page
                  </p>
                </td>
              </tr>
              <tr><td style="height:8px;"></td></tr>
              <tr>
                <td style="padding:12px;background:#f9fafb;
                           border-radius:8px;">
                  <p style="margin:0;font-size:14px;color:#374151;">
                    🔒 &nbsp;Never share this code with anyone
                  </p>
                </td>
              </tr>
            </table>

            <!-- Warning -->
            <div style="background:#fff7ed;border-left:4px solid #f97316;
                        border-radius:0 8px 8px 0;padding:14px 16px;
                        margin-bottom:28px;">
              <p style="margin:0;font-size:13px;color:#9a3412;
                        line-height:1.5;">
                <strong>Security notice:</strong> If you did not create
                an account with {APP_NAME}, please ignore this email.
                Your email address will not be used.
              </p>
            </div>

          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f9fafb;padding:20px 40px;
                     border-top:1px solid #e5e7eb;text-align:center;">
            <p style="margin:0;font-size:12px;color:#9ca3af;
                      line-height:1.6;">
              This email was sent by <strong>{APP_NAME}</strong>.<br/>
              © 2026 {APP_NAME}. All rights reserved.
            </p>
          </td>
        </tr>

      </table>
      <!-- End Card -->

    </td></tr>
  </table>

</body>
</html>
"""