import re
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class StrongPasswordValidator:
    """
    Enforce password rules for all users:
    - length > 6
    - at least one uppercase, one lowercase
    - must contain '!' character
    """

    def validate(self, password: str, user: Any = None) -> None:
        if len(password) <= 6:
            raise ValidationError(
                _("Password must be longer than 6 characters."),
                code="password_too_short",
            )
        if not re.search(r"[A-Z]", password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code="password_no_upper",
            )
        if not re.search(r"[a-z]", password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code="password_no_lower",
            )
        if "!" not in password:
            raise ValidationError(
                _("Password must include the '!' character."),
                code="password_no_exclamation",
            )

    def get_help_text(self) -> str:
        return _(
            "Your password must be longer than 6 characters and contain at least one "
            "uppercase letter, one lowercase letter, and the '!' character."
        )


def validate_sce_email(value: str) -> None:
    """
    Validate that email is from SCE academic domain.
    Emails ending with @sce.ac.il or @ac.sce.ac.il are allowed.
    """
    if not (value.endswith("@sce.ac.il") or value.endswith("@ac.sce.ac.il")):
        raise ValidationError(
            _("Email must be from SCE academic domain (@sce.ac.il or @ac.sce.ac.il). "
              "Please use your official college email address."),
            code="invalid_email_domain",
        )
    
    # Additional check: no dot immediately before @
    if re.search(r"\.\@", value):
        raise ValidationError(
            _("Email must not contain a dot immediately before '@'."),
            code="invalid_email_pattern",
        )
