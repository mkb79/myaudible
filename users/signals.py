from django.contrib.sessions.models import Session
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from core.login import session_pool


@receiver(pre_delete, sender=Session)
def delete_login_session(sender, instance, **kwargs):
    session_id = instance.session_key
    session_pool.remove_session(session_id)

