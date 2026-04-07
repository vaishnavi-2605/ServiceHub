DEFAULT_CATEGORIES = [
    'Plumber',
    'Tutor',
    'Cleaning',
    'AC Repair',
    'Carpenter',
    'Cosmetology',
    'Painter',
    'Pest Control',
    'Appliance Repair',
    'Salon',
]

SERVICE_SUBCATEGORY_MAP = {
    'Plumber': [
        'Pipe Repair',
        'Toilet Repair',
        'Tap Installation',
        'Drain Cleaning',
        'Water Tank Fitting',
        'Other',
    ],
    'Tutor': [
        'Math Tutor',
        'Science Tutor',
        'English Tutor',
        'Computer Tutor',
        'Exam Preparation',
        'Other',
    ],
    'Cleaning': [
        'Home Cleaning',
        'Bathroom Cleaning',
        'Kitchen Cleaning',
        'Sofa Cleaning',
        'Deep Cleaning',
        'Other',
    ],
    'AC Repair': [
        'AC Installation',
        'Gas Refill',
        'Cooling Issue Repair',
        'AC Maintenance',
        'AC Cleaning',
        'Other',
    ],
    'Carpenter': [
        'Furniture Repair',
        'Door Repair',
        'Window Work',
        'Modular Furniture',
        'Wood Polishing',
        'Other',
    ],
    'Cosmetology': [
        'Hair Styling',
        'Bridal Makeup',
        'Facial Treatment',
        'Skin Care',
        'Nail Care',
        'Pedicure',
        'Other',
    ],
}


CATEGORY_ICON_MAP = {
    'plumber': '\U0001F527',
    'tutor': '\U0001F4DA',
    'cleaning': '\U0001F9F9',
    'ac repair': '\u2744\ufe0f',
    'carpenter': '\U0001FA9A',
    'cosmetology': '\U0001F484',
    'painter': '\U0001F3A8',
    'pest control': '\U0001F6E1\ufe0f',
    'appliance repair': '\U0001F50C',
    'salon': '\U0001F487',
}

CANONICAL_CATEGORY_MAP = {
    'cosmetologist': 'Cosmetology',
    'beautician': 'Cosmetology',
    'beauty service': 'Cosmetology',
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


def get_provider_registration_categories():
    return list(DEFAULT_CATEGORIES) + ['Other']
