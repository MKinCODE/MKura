from datetime import datetime
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.config import settings


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
):
    message = MIMEMultipart("alternative")
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(text_content or "", "plain"))
    message.attach(MIMEText(html_content, "html"))

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
        )
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
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
            .content {{ padding: 30px; }}
            .details-box {{ background: #f8f9fa; border-left: 4px solid #3949ab; padding: 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }}
            .detail-row {{ display: flex; margin: 10px 0; }}
            .detail-label {{ font-weight: 600; color: #555; width: 120px; }}
            .detail-value {{ color: #333; }}
            .cancel-btn {{ display: inline-block; background: #fff; color: #d32f2f; border: 2px solid #d32f2f; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: 600; margin-top: 20px; }}
            .cancel-btn:hover {{ background: #d32f2f; color: white; }}
            .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>MK Health Clinic</h1>
                <p>Appointment Confirmed</p>
            </div>
            <div class="content">
                <p>Dear <strong>{patient_name}</strong>,</p>
                <p>Your appointment has been successfully booked! Here are your appointment details:</p>

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

                <p>Please arrive at least 15 minutes before your scheduled appointment time.</p>

                <p>Need to cancel? Click the button below:</p>
                <center>
                    <a href="{cancellation_link}" class="cancel-btn">Cancel Appointment</a>
                </center>
            </div>
            <div class="footer">
                <p>MK Health Clinic | Sector 21, Gandhinagar, Jaipur, Rajasthan</p>
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
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: #d32f2f; color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content {{ padding: 30px; text-align: center; }}
            .check {{ font-size: 60px; color: #4caf50; }}
            .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Appointment Cancelled</h1>
            </div>
            <div class="content">
                <div class="check">✓</div>
                <p>Dear <strong>{patient_name}</strong>,</p>
                <p>Your appointment has been successfully cancelled.</p>
                <p>If you did not request this cancellation, please contact us immediately.</p>
            </div>
            <div class="footer">
                <p>MK Health Clinic | Sector 21, Gandhinagar, Jaipur, Rajasthan</p>
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
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #ff6f00 0%, #ff8f00 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content {{ padding: 30px; }}
            .highlight {{ background: #fff3e0; border: 2px solid #ff9800; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; }}
            .time {{ font-size: 28px; font-weight: bold; color: #e65100; }}
            .urgent {{ color: #d32f2f; font-weight: bold; }}
            .btn-container {{ text-align: center; margin-top: 20px; }}
            .btn {{ display: inline-block; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: 600; margin: 0 10px; }}
            .btn-accept {{ background: #4caf50; color: white; }}
            .btn-decline {{ background: #fff; color: #d32f2f; border: 2px solid #d32f2f; }}
            .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Earlier Slot Available!</h1>
            </div>
            <div class="content">
                <p>Dear <strong>{patient_name}</strong>,</p>
                <p>Great news! A slot has become available earlier than your current booking.</p>

                <div class="highlight">
                    <p><strong>{doctor_name}</strong></p>
                    <p class="time">{date} at {time}</p>
                </div>

                <p class="urgent">⏰ This offer expires in {expires_in_minutes} minutes!</p>

                <div class="btn-container">
                    <a href="{accept_link}" class="btn btn-accept">Accept Slot</a>
                    <a href="{decline_link}" class="btn btn-decline">Decline</a>
                </div>
            </div>
            <div class="footer">
                <p>MK Health Clinic | Sector 21, Gandhinagar, Jaipur, Rajasthan</p>
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
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #00897b 0%, #26a69a 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content {{ padding: 30px; }}
            .details-box {{ background: #f8f9fa; border-left: 4px solid #00897b; padding: 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }}
            .detail-row {{ display: flex; margin: 10px 0; }}
            .detail-label {{ font-weight: 600; color: #555; width: 120px; }}
            .detail-value {{ color: #333; }}
            .reminder {{ background: #e0f2f1; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .cancel-btn {{ display: inline-block; background: #fff; color: #d32f2f; border: 2px solid #d32f2f; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: 600; margin-top: 20px; }}
            .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Appointment Reminder</h1>
            </div>
            <div class="content">
                <p>Dear <strong>{patient_name}</strong>,</p>
                <p>This is a friendly reminder about your upcoming appointment:</p>

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

                <div class="reminder">
                    <strong>⏰ Don't forget!</strong> Your appointment is in 1 hour. Please arrive 15 minutes early.
                </div>

                <p>Need to cancel? <a href="{cancellation_link}">Click here to cancel</a></p>
            </div>
            <div class="footer">
                <p>MK Health Clinic | Sector 21, Gandhinagar, Jaipur, Rajasthan</p>
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
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #7b1fa2 0%, #9c27b0 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content {{ padding: 30px; }}
            .changes {{ display: flex; align-items: center; justify-content: center; margin: 20px 0; }}
            .old {{ background: #ffebee; padding: 15px 25px; border-radius: 8px; text-decoration: line-through; color: #999; }}
            .arrow {{ font-size: 30px; margin: 0 20px; color: #4caf50; }}
            .new {{ background: #e8f5e9; padding: 15px 25px; border-radius: 8px; color: #2e7d32; font-weight: bold; }}
            .notice {{ background: #fff3e0; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .cancel-btn {{ display: inline-block; background: #fff; color: #d32f2f; border: 2px solid #d32f2f; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: 600; margin-top: 20px; }}
            .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Appointment Rescheduled</h1>
            </div>
            <div class="content">
                <p>Dear <strong>{patient_name}</strong>,</p>
                <p>Your appointment with <strong>{doctor_name}</strong> has been rescheduled due to an emergency.</p>

                <div class="changes">
                    <span class="old">{old_date} at {old_time}</span>
                    <span class="arrow">→</span>
                    <span class="new">{new_date} at {new_time}</span>
                </div>

                <div class="notice">
                    We apologize for any inconvenience. If the new time doesn't work for you, you may cancel and rebook at your convenience.
                </div>

                <center>
                    <a href="{cancellation_link}" class="cancel-btn">Cancel Appointment</a>
                </center>
            </div>
            <div class="footer">
                <p>MK Health Clinic | Sector 21, Gandhinagar, Jaipur, Rajasthan</p>
            </div>
        </div>
    </body>
    </html>
    """