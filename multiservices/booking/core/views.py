from django.shortcuts import render
from services.constants import get_category_icon, normalize_category_name
from services.models import Service


# def hello(request):
#     return HttpResponse("Hello, welcome to the core app!")


def home(request):
    main_home_categories = [
        'Plumber',
        'Tutor',
        'Cleaning',
        'AC Repair',
        'Carpenter',
    ]

    def _category_key(value):
        return normalize_category_name(value).strip().lower()

    db_categories = list(Service.objects.order_by('name').values_list('name', flat=True).distinct())
    seen_keys = {_category_key(cat) for cat in main_home_categories}
    all_categories = list(main_home_categories)
    for cat in db_categories:
        normalized_cat = normalize_category_name(cat)
        if normalized_cat.lower() == 'electrical':
            continue
        cat_key = _category_key(normalized_cat)
        if not cat_key or cat_key in seen_keys:
            continue
        seen_keys.add(cat_key)
        all_categories.append(normalized_cat)

    category_image_map = {}
    service_images = Service.objects.exclude(image='').exclude(image__isnull=True).order_by('-created_at')
    for item in service_images:
        item_key = _category_key(item.name)
        if item_key and item_key not in category_image_map:
            category_image_map[item_key] = item.image.url

    home_categories = []
    for category_name in all_categories:
        category_key = _category_key(category_name)
        home_categories.append({
            'name': category_name,
            'icon': get_category_icon(category_name),
            'image_url': category_image_map.get(category_key),
        })

    return render(request, "core/index.html", {"home_categories": home_categories[:10]})
