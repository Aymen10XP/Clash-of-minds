"""Helpers for recording application actions that need an audit trail."""

from .models import AuditEvent


def record_audit_event(*, actor, action, target_type, target_id='', details=None):
    """Persist a minimal, append-only record for a completed sensitive action."""
    return AuditEvent.objects.create(
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else '',
        details=details or {},
    )
