"""Notification sending, abstracted so a real email/SMS provider can be swapped in later.

Runs via FastAPI BackgroundTasks so checkout responses aren't blocked on I/O.
"""
import logging

logger = logging.getLogger("commerce.notifications")


async def send_order_confirmation(email: str, order_id: str, total_amount: str) -> None:
    # Replace with a real provider (SES, SendGrid, Postmark, etc.) — interface stays the same.
    logger.info("Order confirmation -> %s | order=%s | total=%s", email, order_id, total_amount)
