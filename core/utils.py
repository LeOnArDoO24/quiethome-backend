from rest_framework.exceptions import ValidationError

def validate_image_size(value):
    limit_mb = 2
    if value.size > limit_mb * 1024 * 1024:
        raise ValidationError(f"L'immagine non può superare {limit_mb}MB.")