# users/templatetags/forms_extras.py
from django import template
from django.utils.safestring import SafeString
from django.utils.html import conditional_escape

register = template.Library()

@register.filter(name="add_class")
def add_class(field, css):
    """
    Ajoute une ou plusieurs classes au widget d'un BoundField.
    - Si on reçoit déjà du HTML (SafeString), on le renvoie tel quel
      pour éviter l'erreur lors d'un chainage malheureux.
    Usage: {{ field|add_class:"form-control auth-input" }}
    """
    # Si c'est déjà du HTML rendu, on ne peut plus appeler as_widget
    if isinstance(field, SafeString) or not hasattr(field, "as_widget"):
        return field

    # Récupère les attrs existants du widget
    attrs = getattr(field.field.widget, "attrs", {}).copy()
    existing = attrs.get("class", "").strip()

    # Fusionne les classes
    extra = (css or "").strip()
    merged = (existing + " " + extra).strip() if existing else extra

    attrs["class"] = merged
    return field.as_widget(attrs=attrs)
