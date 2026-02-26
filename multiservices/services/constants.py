DEFAULT_CATEGORIES = [
    'Plumber',
    'Tutor',
    'Cleaning',
    'AC Repair',
    'Carpenter',
    'Painter',
    'Pest Control',
    'Appliance Repair',
    'Salon',
]


CATEGORY_ICON_MAP = {
    'plumber': '\U0001F527',
    'tutor': '\U0001F4DA',
    'cleaning': '\U0001F9F9',
    'ac repair': '\u2744\ufe0f',
    'carpenter': '\U0001FA9A',
    'painter': '\U0001F3A8',
    'pest control': '\U0001F6E1\ufe0f',
    'appliance repair': '\U0001F50C',
    'salon': '\U0001F487',
}

CANONICAL_CATEGORY_MAP = {
}


def normalize_category_name(category_name):
    if not category_name:
        return ''

    normalized = ' '.join(str(category_name).split()).strip()
    if not normalized:
        return ''

    normalized_lower = normalized.lower()
    if normalized_lower in CANONICAL_CATEGORY_MAP:
        return CANONICAL_CATEGORY_MAP[normalized_lower]

    for category in DEFAULT_CATEGORIES:
        if normalized_lower == category.lower():
            return category

    return normalized


def get_category_match_terms(category_name):
    normalized = normalize_category_name(category_name)
    if not normalized:
        return []

    key = normalized.lower()
    return [key]


def get_category_icon(category_name):
    if not category_name:
        return '\U0001F6E0\ufe0f'

    name_lower = normalize_category_name(category_name).strip().lower()
    for key, icon in CATEGORY_ICON_MAP.items():
        if key in name_lower or name_lower in key:
            return icon
    return '\U0001F6E0\ufe0f'
