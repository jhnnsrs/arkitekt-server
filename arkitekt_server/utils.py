from slugify import slugify


def safe_org_slug(name: str, max_length: int = 8) -> str:
    return slugify(
        name.lower(),
        separator="_",
        regex_pattern=r"[^a-z_]+",  # ✅ allow only lowercase letters and underscores
    )[:max_length]
