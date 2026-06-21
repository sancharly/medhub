"""Email template rendering (TASK-031).

Produces plain-text email bodies. No HTML templating engine required
for this phase — keeping it simple.
"""

from __future__ import annotations


def render_activation_email(
    first_name: str | None,
    activation_link: str,
) -> tuple[str, str]:
    """Return (subject, body) for an account activation email."""
    name = first_name or "there"
    subject = "Activate your MedHub account"
    body = (
        f"Hi {name},\n\n"
        "Welcome to MedHub. Please activate your account by visiting the link below.\n"
        "This link expires in 72 hours.\n\n"
        f"  {activation_link}\n\n"
        "If you did not create this account, you can safely ignore this email.\n\n"
        "— The MedHub Team"
    )
    return subject, body


def render_appointment_notification(
    patient_name: str | None,
    doctor_name: str | None,
    scheduled_at_str: str,
    appointment_link: str,
) -> tuple[str, str]:
    """Return (subject, body) for an appointment notification email."""
    patient = patient_name or "Patient"
    doctor = doctor_name or "your doctor"
    subject = "Your MedHub appointment"
    body = (
        f"Hi {patient},\n\n"
        f"Your appointment with {doctor} has been scheduled for {scheduled_at_str}.\n\n"
        f"View details: {appointment_link}\n\n"
        "— The MedHub Team"
    )
    return subject, body
