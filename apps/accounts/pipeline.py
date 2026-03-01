def save_google_user(backend, user, response, *args, **kwargs):
    """Set verified + google flag. Never overwrite existing role."""
    if backend.name != 'google-oauth2':
        return

    changed = False

    if not user.is_verified:
        user.is_verified = True
        changed = True

    if not user.is_google:
        user.is_google = True
        changed = True

    if not user.is_active:
        user.is_active = True
        changed = True

    # ← KEY FIX: never touch role if already set
    # Only set default if user has NO role at all
    # (do NOT set here — let social_complete_view handle it)

    if changed:
        user.save()