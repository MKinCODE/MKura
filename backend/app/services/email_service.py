from datetime import datetime
from typing import Optional
import resend
from ..core.config import settings

# Configure Resend API key at module level
resend.api_key = settings.RESEND_API_KEY


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
):
    try:
        params: resend.Emails.SendParams = {
            "from": settings.FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        if text_content:
            params["text"] = text_content

        email = resend.Emails.send(params)
        print(f"Email sent successfully via Resend: {email.get('id', 'unknown')}")
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


def get_booking_confirmation_html(
    patient_name: str,
    doctor_name: str,
    specialization: str,
    date: str,
    time: str,
    clinic_address: str,
    cancellation_link: str,
    clinic_phone: str,
) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', system-ui, -apple-system, Roboto, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; -webkit-font-smoothing: antialiased; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); border: 1px solid #f1f5f9; }}
            .header {{ background: linear-gradient(135deg, #1e1b4b 0%, #4f46e5 100%); color: white; padding: 40px 30px; text-align: center; }}
            .logo-wrapper {{ display: inline-flex; align-items: center; background: rgba(255, 255, 255, 0.12); padding: 8px 18px; border-radius: 50px; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.15); }}
            .logo-icon {{ font-size: 20px; margin-right: 8px; line-height: 1; }}
            .logo-text {{ font-size: 14px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2; }}
            .header p {{ margin: 8px 0 0 0; font-size: 15px; color: #c7d2fe; font-weight: 500; }}
            .content {{ padding: 40px 35px; color: #334155; line-height: 1.6; font-size: 15px; }}
            .greeting {{ font-size: 18px; font-weight: 600; color: #0f172a; margin-top: 0; margin-bottom: 12px; }}
            .details-box {{ background: #f8fafc; border-left: 4px solid #4f46e5; padding: 25px; margin: 25px 0; border-radius: 0 12px 12px 0; border-top: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; }}
            .detail-row {{ display: flex; margin: 12px 0; }}
            .detail-row:first-child {{ margin-top: 0; }}
            .detail-row:last-child {{ margin-bottom: 0; }}
            .detail-label {{ font-weight: 600; color: #64748b; width: 110px; flex-shrink: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
            .detail-value {{ color: #0f172a; font-weight: 500; }}
            .action-btn {{ display: inline-block; background-color: #ef4444; color: #ffffff; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 14px; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15); transition: all 0.2s ease; margin-top: 15px; }}
            .footer {{ text-align: center; padding: 30px; color: #64748b; font-size: 12px; background-color: #f8fafc; border-top: 1px solid #f1f5f9; line-height: 1.5; }}
            .footer-name {{ font-weight: 700; color: #475569; font-size: 13px; margin: 0 0 6px 0; letter-spacing: 0.5px; }}
            .footer-address {{ margin: 0 0 6px 0; }}
            .footer-contact {{ margin: 0; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo-wrapper">
                    <span class="logo-icon">🩺</span>
                    <span class="logo-text">MK Health Clinic</span>
                </div>
                <h1>Appointment Confirmed</h1>
                <p>We look forward to seeing you</p>
            </div>
            <div class="content">
                <p class="greeting">Dear {patient_name},</p>
                <p>Your appointment has been successfully booked. Below are the details of your scheduled visit:</p>

                <div class="details-box">
                    <div class="detail-row">
                        <span class="detail-label">Doctor:</span>
                        <span class="detail-value">{doctor_name} ({specialization})</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Date:</span>
                        <span class="detail-value">{date}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Time:</span>
                        <span class="detail-value">{time}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Location:</span>
                        <span class="detail-value">{clinic_address}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Phone:</span>
                        <span class="detail-value">{clinic_phone}</span>
                    </div>
                </div>

                <p style="margin-bottom: 25px;">Please arrive at least 15 minutes before your scheduled appointment time. If you need to make changes or cancel, please use the secure button below.</p>

                <center>
                    <a href="{cancellation_link}" class="action-btn">Cancel Appointment</a>
                </center>
            </div>
            <div class="footer">
                <p class="footer-name">MK Health Clinic</p>
                <p class="footer-address">Sector 21, Gandhinagar, Jaipur, Rajasthan 302015</p>
                <p class="footer-contact">Phone: {clinic_phone} | Patient Care Portal</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_cancellation_confirmed_html(patient_name: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', system-ui, -apple-system, Roboto, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; -webkit-font-smoothing: antialiased; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); border: 1px solid #f1f5f9; }}
            .header {{ background: #fef2f2; border-bottom: 2px solid #fee2e2; color: #991b1b; padding: 40px 30px; text-align: center; }}
            .logo-wrapper {{ display: inline-flex; align-items: center; background: #fee2e2; padding: 8px 18px; border-radius: 50px; margin-bottom: 20px; border: 1px solid #fecaca; }}
            .logo-icon {{ font-size: 20px; margin-right: 8px; line-height: 1; }}
            .logo-text {{ font-size: 14px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #991b1b; }}
            .header h1 {{ margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2; }}
            .header p {{ margin: 8px 0 0 0; font-size: 15px; color: #ef4444; font-weight: 500; }}
            .content {{ padding: 40px 35px; color: #334155; line-height: 1.6; font-size: 15px; text-align: center; }}
            .greeting {{ font-size: 18px; font-weight: 600; color: #0f172a; margin-top: 0; margin-bottom: 12px; }}
            .cancel-badge {{ display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; background-color: #fef2f2; border-radius: 50%; color: #ef4444; font-size: 32px; margin-bottom: 20px; border: 2px solid #fee2e2; }}
            .footer {{ text-align: center; padding: 30px; color: #64748b; font-size: 12px; background-color: #f8fafc; border-top: 1px solid #f1f5f9; line-height: 1.5; }}
            .footer-name {{ font-weight: 700; color: #475569; font-size: 13px; margin: 0 0 6px 0; letter-spacing: 0.5px; }}
            .footer-address {{ margin: 0 0 6px 0; }}
            .footer-contact {{ margin: 0; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo-wrapper">
                    <span class="logo-icon">🩺</span>
                    <span class="logo-text">MK Health Clinic</span>
                </div>
                <h1>Appointment Cancelled</h1>
                <p>Booking cancellation confirmed</p>
            </div>
            <div class="content">
                <div class="cancel-badge">✓</div>
                <p class="greeting">Dear {patient_name},</p>
                <p>Your appointment has been successfully cancelled as requested. Any pre-authorized payment holds will be automatically released or refunded back to your account.</p>
                <p style="margin-bottom: 0; color: #64748b; font-size: 14px;">If you did not request this cancellation or would like to book a new appointment, please visit our online patient portal.</p>
            </div>
            <div class="footer">
                <p class="footer-name">MK Health Clinic</p>
                <p class="footer-address">Sector 21, Gandhinagar, Jaipur, Rajasthan 302015</p>
                <p class="footer-contact">Patient Care Portal</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_upgradation_offer_html(
    patient_name: str,
    doctor_name: str,
    date: str,
    time: str,
    accept_link: str,
    decline_link: str,
    expires_in_minutes: int = 15,
) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', system-ui, -apple-system, Roboto, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; -webkit-font-smoothing: antialiased; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); border: 1px solid #f1f5f9; }}
            .header {{ background: linear-gradient(135deg, #7c2d12 0%, #ea580c 100%); color: white; padding: 40px 30px; text-align: center; }}
            .logo-wrapper {{ display: inline-flex; align-items: center; background: rgba(255, 255, 255, 0.12); padding: 8px 18px; border-radius: 50px; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.15); }}
            .logo-icon {{ font-size: 20px; margin-right: 8px; line-height: 1; }}
            .logo-text {{ font-size: 14px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2; }}
            .header p {{ margin: 8px 0 0 0; font-size: 15px; color: #ffedd5; font-weight: 500; }}
            .content {{ padding: 40px 35px; color: #334155; line-height: 1.6; font-size: 15px; }}
            .greeting {{ font-size: 18px; font-weight: 600; color: #0f172a; margin-top: 0; margin-bottom: 12px; }}
            .highlight-box {{ background: #fffbeb; border: 2px solid #f59e0b; border-radius: 12px; padding: 25px; margin: 25px 0; text-align: center; }}
            .doctor-name {{ font-size: 18px; font-weight: 700; color: #78350f; margin: 0 0 6px 0; }}
            .slot-time {{ font-size: 26px; font-weight: 800; color: #d97706; margin: 0; letter-spacing: -0.5px; }}
            .urgent-banner {{ background: #fef2f2; border: 1px solid #fee2e2; border-radius: 8px; padding: 12px 15px; color: #b91c1c; font-weight: 600; text-align: center; margin: 20px 0; font-size: 14px; }}
            .btn-group {{ text-align: center; margin-top: 25px; }}
            .btn {{ display: inline-block; padding: 14px 30px; border-radius: 10px; text-decoration: none; font-weight: 700; font-size: 14px; margin: 6px; transition: all 0.2s ease; }}
            .btn-accept {{ background-color: #22c55e; color: #ffffff; box-shadow: 0 4px 12px rgba(34, 197, 94, 0.2); }}
            .btn-decline {{ background-color: #ffffff; color: #ef4444; border: 2px solid #ef4444; }}
            .footer {{ text-align: center; padding: 30px; color: #64748b; font-size: 12px; background-color: #f8fafc; border-top: 1px solid #f1f5f9; line-height: 1.5; }}
            .footer-name {{ font-weight: 700; color: #475569; font-size: 13px; margin: 0 0 6px 0; letter-spacing: 0.5px; }}
            .footer-address {{ margin: 0 0 6px 0; }}
            .footer-contact {{ margin: 0; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo-wrapper">
                    <span class="logo-icon">🩺</span>
                    <span class="logo-text">MK Health Clinic</span>
                </div>
                <h1>Earlier Slot Available!</h1>
                <p>Waitlist Priority Upgrade Offer</p>
            </div>
            <div class="content">
                <p class="greeting">Dear {patient_name},</p>
                <p>Good news! An earlier appointment slot has just opened up with your doctor. As a valued waitlist patient, we are extending a priority offer to upgrade your booking:</p>

                <div class="highlight-box">
                    <p class="doctor-name">{doctor_name}</p>
                    <p class="slot-time">{date} at {time}</p>
                </div>

                <div class="urgent-banner">
                    ⏰ Rapid Response Required: This invitation is waitlist-exclusive and will expire in {expires_in_minutes} minutes.
                </div>

                <p style="font-size: 14px; color: #64748b; margin-bottom: 25px; text-align: center;">If you accept, your old booking will be automatically swapped to this earlier time. If you decline or ignore this, you will keep your original booking without any changes.</p>

                <div class="btn-group">
                    <a href="{accept_link}" class="btn btn-accept">Accept Earlier Slot</a>
                    <a href="{decline_link}" class="btn btn-decline">Keep My Current Slot</a>
                </div>
            </div>
            <div class="footer">
                <p class="footer-name">MK Health Clinic</p>
                <p class="footer-address">Sector 21, Gandhinagar, Jaipur, Rajasthan 302015</p>
                <p class="footer-contact">Waitlist Automation System</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_reminder_html(
    patient_name: str,
    doctor_name: str,
    specialization: str,
    date: str,
    time: str,
    cancellation_link: str,
) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', system-ui, -apple-system, Roboto, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; -webkit-font-smoothing: antialiased; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); border: 1px solid #f1f5f9; }}
            .header {{ background: linear-gradient(135deg, #064e3b 0%, #0d9488 100%); color: white; padding: 40px 30px; text-align: center; }}
            .logo-wrapper {{ display: inline-flex; align-items: center; background: rgba(255, 255, 255, 0.12); padding: 8px 18px; border-radius: 50px; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.15); }}
            .logo-icon {{ font-size: 20px; margin-right: 8px; line-height: 1; }}
            .logo-text {{ font-size: 14px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2; }}
            .header p {{ margin: 8px 0 0 0; font-size: 15px; color: #ccfbf1; font-weight: 500; }}
            .content {{ padding: 40px 35px; color: #334155; line-height: 1.6; font-size: 15px; }}
            .greeting {{ font-size: 18px; font-weight: 600; color: #0f172a; margin-top: 0; margin-bottom: 12px; }}
            .details-box {{ background: #f8fafc; border-left: 4px solid #0d9488; padding: 25px; margin: 25px 0; border-radius: 0 12px 12px 0; border-top: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; }}
            .detail-row {{ display: flex; margin: 12px 0; }}
            .detail-row:first-child {{ margin-top: 0; }}
            .detail-row:last-child {{ margin-bottom: 0; }}
            .detail-label {{ font-weight: 600; color: #64748b; width: 110px; flex-shrink: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
            .detail-value {{ color: #0f172a; font-weight: 500; }}
            .alert-box {{ background: #f0fdf4; border: 1px solid #dcfce7; border-radius: 8px; padding: 15px; color: #166534; font-weight: 600; margin: 20px 0; font-size: 14px; text-align: center; }}
            .footer {{ text-align: center; padding: 30px; color: #64748b; font-size: 12px; background-color: #f8fafc; border-top: 1px solid #f1f5f9; line-height: 1.5; }}
            .footer-name {{ font-weight: 700; color: #475569; font-size: 13px; margin: 0 0 6px 0; letter-spacing: 0.5px; }}
            .footer-address {{ margin: 0 0 6px 0; }}
            .footer-contact {{ margin: 0; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo-wrapper">
                    <span class="logo-icon">🩺</span>
                    <span class="logo-text">MK Health Clinic</span>
                </div>
                <h1>Appointment Reminder</h1>
                <p>We look forward to seeing you soon</p>
            </div>
            <div class="content">
                <p class="greeting">Dear {patient_name},</p>
                <p>This is a friendly reminder that you have an upcoming appointment scheduled with us shortly:</p>

                <div class="details-box">
                    <div class="detail-row">
                        <span class="detail-label">Doctor:</span>
                        <span class="detail-value">{doctor_name} ({specialization})</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Date:</span>
                        <span class="detail-value">{date}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Time:</span>
                        <span class="detail-value">{time}</span>
                    </div>
                </div>

                <div class="alert-box">
                    ⏰ Don't forget! Your appointment is scheduled to start in 1 hour.
                </div>

                <p style="margin-bottom: 25px; font-size: 14px; color: #64748b; text-align: center;">Please try to arrive 15 minutes before your scheduled start time. If you need to cancel, you can do so by clicking the link below:</p>
                <center>
                    <a href="{cancellation_link}" style="color: #ef4444; font-weight: 600; text-decoration: underline;">Cancel Appointment</a>
                </center>
            </div>
            <div class="footer">
                <p class="footer-name">MK Health Clinic</p>
                <p class="footer-address">Sector 21, Gandhinagar, Jaipur, Rajasthan 302015</p>
                <p class="footer-contact">Patient Care Portal</p>
            </div>
        </div>
    </body>
    </html>
    """


def get_reschedule_notification_html(
    patient_name: str,
    old_date: str,
    old_time: str,
    new_date: str,
    new_time: str,
    doctor_name: str,
    cancellation_link: str,
) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', system-ui, -apple-system, Roboto, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; -webkit-font-smoothing: antialiased; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); border: 1px solid #f1f5f9; }}
            .header {{ background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%); color: white; padding: 40px 30px; text-align: center; }}
            .logo-wrapper {{ display: inline-flex; align-items: center; background: rgba(255, 255, 255, 0.12); padding: 8px 18px; border-radius: 50px; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.15); }}
            .logo-icon {{ font-size: 20px; margin-right: 8px; line-height: 1; }}
            .logo-text {{ font-size: 14px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2; }}
            .header p {{ margin: 8px 0 0 0; font-size: 15px; color: #ddd6fe; font-weight: 500; }}
            .content {{ padding: 40px 35px; color: #334155; line-height: 1.6; font-size: 15px; }}
            .greeting {{ font-size: 18px; font-weight: 600; color: #0f172a; margin-top: 0; margin-bottom: 12px; }}
            .changes-box {{ display: flex; align-items: center; justify-content: center; margin: 25px 0; background: #fafafa; padding: 20px; border-radius: 12px; border: 1px solid #f1f5f9; }}
            .old-time {{ background: #fee2e2; padding: 12px 18px; border-radius: 8px; text-decoration: line-through; color: #991b1b; font-weight: 500; font-size: 14px; }}
            .arrow {{ font-size: 24px; margin: 0 15px; color: #94a3b8; }}
            .new-time {{ background: #dcfce7; padding: 12px 18px; border-radius: 8px; color: #166534; font-weight: 700; font-size: 14px; }}
            .notice-box {{ background: #fffbeb; border: 1px solid #fef3c7; border-radius: 8px; padding: 15px; color: #b45309; margin: 20px 0; font-size: 14px; }}
            .action-btn {{ display: inline-block; background-color: #ef4444; color: #ffffff; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 14px; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15); transition: all 0.2s ease; margin-top: 15px; }}
            .footer {{ text-align: center; padding: 30px; color: #64748b; font-size: 12px; background-color: #f8fafc; border-top: 1px solid #f1f5f9; line-height: 1.5; }}
            .footer-name {{ font-weight: 700; color: #475569; font-size: 13px; margin: 0 0 6px 0; letter-spacing: 0.5px; }}
            .footer-address {{ margin: 0 0 6px 0; }}
            .footer-contact {{ margin: 0; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo-wrapper">
                    <span class="logo-icon">🩺</span>
                    <span class="logo-text">MK Health Clinic</span>
                </div>
                <h1>Appointment Rescheduled</h1>
                <p>Important update regarding your visit</p>
            </div>
            <div class="content">
                <p class="greeting">Dear {patient_name},</p>
                <p>Please note that your upcoming appointment with <strong>{doctor_name}</strong> has been rescheduled due to an unexpected clinical schedule adjustment:</p>

                <div class="changes-box">
                    <span class="old-time">{old_date} at {old_time}</span>
                    <span class="arrow">→</span>
                    <span class="new-time">{new_date} at {new_time}</span>
                </div>

                <div class="notice-box">
                    ⚠️ We apologize for any inconvenience. If this new time does not work for you, you can cancel this appointment and reschedule another slot at your convenience.
                </div>

                <p style="margin-bottom: 25px; text-align: center;">If you'd like to cancel, please click the button below:</p>

                <center>
                    <a href="{cancellation_link}" class="action-btn">Cancel Appointment</a>
                </center>
            </div>
            <div class="footer">
                <p class="footer-name">MK Health Clinic</p>
                <p class="footer-address">Sector 21, Gandhinagar, Jaipur, Rajasthan 302015</p>
                <p class="footer-contact">Patient Care Portal</p>
            </div>
        </div>
    </body>
    </html>
    """