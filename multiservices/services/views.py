from decimal import Decimal, InvalidOperation
import re
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Count
from django.urls import reverse
from django.utils import timezone
from booking.models import Booking
from accounts.models import ProviderProfile
from notifications.models import Notification

from .models import Service
from .forms import ProviderServiceForm
from .constants import DEFAULT_CATEGORIES, get_category_icon, get_category_match_terms, normalize_category_name

INDIA_LAT_MIN = Decimal('6.0')
INDIA_LAT_MAX = Decimal('38.5')
INDIA_LNG_MIN = Decimal('68.0')
INDIA_LNG_MAX = Decimal('98.0')


# def hello(request):
#     return HttpResponse('Hello, welcome to the services app!')


def _parse_time_value(raw_value):
    if not raw_value:
        return None
    value = str(raw_value).strip().upper()
    value = re.sub(r'\s+', ' ', value)
    for fmt in ('%H:%M', '%I:%M %p', '%I:%M%p', '%I %p', '%I%p'):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None


def _parse_available_window(raw_range):
    if not raw_range:
        return None
    normalized = str(raw_range).strip()
    if not normalized:
        return None
    normalized = normalized.replace(' to ', '-').replace(' TO ', '-').replace('–', '-').replace('—', '-')
    parts = [p.strip() for p in normalized.split('-', 1)]
    if len(parts) != 2:
        return None
    start_time = _parse_time_value(parts[0])
    end_time = _parse_time_value(parts[1])
    if not start_time or not end_time:
        return None
    return start_time, end_time


def _is_time_in_window(target_time, start_time, end_time):
    if start_time <= end_time:
        return start_time <= target_time <= end_time
    return target_time >= start_time or target_time <= end_time


def _is_india_coordinate(lat_value, lng_value):
    return (
        INDIA_LAT_MIN <= lat_value <= INDIA_LAT_MAX
        and INDIA_LNG_MIN <= lng_value <= INDIA_LNG_MAX
    )


def service(request):
    query = request.GET.get('q', '').strip()
    category = normalize_category_name(request.GET.get('category', '').strip())
    max_price = request.GET.get('max_price', '').strip()
    min_rating = request.GET.get('min_rating', '').strip()
    sort = request.GET.get('sort', '').strip()

    mapped_query_to_category = False
    if query and not category:
        q_lower = query.lower()
        for cat in DEFAULT_CATEGORIES:
            if q_lower in cat.lower() or cat.lower() in q_lower:
                category = cat
                mapped_query_to_category = True
                break

    if mapped_query_to_category:
        # Once query maps to a category, keep results category-based instead of text-restricted.
        query = ''

    services_qs = Service.objects.select_related('provider').filter(
        provider__is_active=True,
        provider__provider_status='approved',
    )

    if query and not mapped_query_to_category:
        services_qs = services_qs.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(provider__first_name__icontains=query)
            | Q(provider__username__icontains=query)
        )

    if category:
        category_terms = get_category_match_terms(category)
        if category_terms:
            category_filter = Q()
            for term in category_terms:
                category_filter |= Q(name__icontains=term)
            services_qs = services_qs.filter(category_filter)

    if max_price:
        try:
            services_qs = services_qs.filter(price__lte=Decimal(max_price))
        except (InvalidOperation, ValueError):
            pass

    services_list = list(services_qs)
    service_ids = [s.id for s in services_list]
    provider_ids = [s.provider_id for s in services_list]
    profile_map = {
        p.user_id: p
        for p in ProviderProfile.objects.filter(user_id__in=provider_ids)
    }
    ratings_map = {
        r['service_id']: r
        for r in Booking.objects.filter(service_id__in=service_ids, feedback_rating__isnull=False)
        .values('service_id')
        .annotate(avg_rating=Avg('feedback_rating'), review_count=Count('id'))
    }

    for s in services_list:
        stats = ratings_map.get(s.id)
        profile = profile_map.get(s.provider_id)
        review_count = stats['review_count'] if stats else 0
        if stats and stats['avg_rating'] is not None and review_count:
            weighted_avg = (float(stats['avg_rating']) * review_count + 3.0) / (review_count + 1)
            s.avg_rating = round(weighted_avg, 1)
            s.is_default_rating = False
        else:
            s.avg_rating = 3.0
            s.is_default_rating = True
        s.review_count = review_count
        s.display_name = normalize_category_name(s.name)
        s.category_icon = get_category_icon(s.display_name)
        s.provider_image_url = profile.profile_image.url if profile and profile.profile_image else None

    if min_rating:
        try:
            min_rating_val = float(min_rating)
            services_list = [s for s in services_list if s.avg_rating is not None and s.avg_rating >= min_rating_val]
        except ValueError:
            pass

    if sort == 'price_low':
        services_list.sort(key=lambda x: x.price)
    elif sort == 'price_high':
        services_list.sort(key=lambda x: x.price, reverse=True)
    elif sort == 'rating_high':
        services_list.sort(key=lambda x: (x.avg_rating is not None, x.avg_rating or 0), reverse=True)
    else:
        services_list.sort(key=lambda x: x.created_at, reverse=True)

    db_categories = list(
        Service.objects.filter(provider__is_active=True, provider__provider_status='approved')
        .order_by('name')
        .values_list('name', flat=True)
        .distinct()
    )
    normalized_db_categories = []
    seen_category_keys = set()
    for cat in db_categories:
        normalized_cat = normalize_category_name(cat)
        if not normalized_cat:
            continue
        cat_key = normalized_cat.lower()
        if cat_key in seen_category_keys:
            continue
        seen_category_keys.add(cat_key)
        normalized_db_categories.append(normalized_cat)

    all_categories = list(dict.fromkeys(DEFAULT_CATEGORIES + normalized_db_categories))

    return render(request, 'services/services.html', {
        'services': services_list,
        'query': query,
        'categories': all_categories,
        'selected_category': category,
        'selected_max_price': max_price,
        'selected_min_rating': min_rating,
        'selected_sort': sort,
    })


def service_detail(request, service_id):
    service_obj = get_object_or_404(
        Service.objects.select_related('provider'),
        id=service_id,
        provider__is_active=True,
        provider__provider_status='approved',
    )
    service_obj.display_name = normalize_category_name(service_obj.name)
    profile = ProviderProfile.objects.filter(user=service_obj.provider).first()

    reviews = Booking.objects.filter(
        service=service_obj,
        feedback_rating__isnull=False
    ).select_related('user').order_by('-created_at')[:10]

    summary = Booking.objects.filter(service=service_obj, feedback_rating__isnull=False).aggregate(
        avg=Avg('feedback_rating'),
        count=Count('id')
    )

    review_count = summary['count'] or 0
    if summary['avg'] is not None and review_count:
        weighted_avg = (float(summary['avg']) * review_count + 3.0) / (review_count + 1)
        avg_rating = round(weighted_avg, 1)
        is_default_rating = False
    else:
        avg_rating = 3.0
        is_default_rating = True
    return render(request, 'services/provider-detail.html', {
        'provider': service_obj.provider,
        'service': service_obj,
        'profile': profile,
        'avg_rating': avg_rating,
        'is_default_rating': is_default_rating,
        'review_count': review_count,
        'reviews': reviews,
        'today_iso': timezone.localdate().isoformat(),
    })


@login_required
def provider_services(request):
    if request.user.role != 'provider':
        return redirect('home')
    if not request.user.is_active:
        logout(request)
        return redirect('home')

    services = Service.objects.filter(provider=request.user).order_by('-created_at')

    if request.method == 'POST':
        form = ProviderServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service_obj = form.save(commit=False)
            service_obj.name = normalize_category_name(service_obj.name)
            service_obj.provider = request.user
            service_obj.save()
            return redirect('provider_dashboard')
    else:
        form = ProviderServiceForm()

    return render(request, 'services/provider-services.html', {
        'form': form,
        'services': services,
    })


@login_required
def edit_provider_service(request, service_id):
    if request.user.role != 'provider':
        return redirect('home')
    if not request.user.is_active:
        logout(request)
        return redirect('home')

    service_obj = get_object_or_404(Service, id=service_id, provider=request.user)

    if request.method == 'POST':
        form = ProviderServiceForm(request.POST, request.FILES, instance=service_obj)
        if form.is_valid():
            updated_service = form.save(commit=False)
            updated_service.name = normalize_category_name(updated_service.name)
            updated_service.save()
            return redirect('provider_services')
    else:
        form = ProviderServiceForm(instance=service_obj)

    services = Service.objects.filter(provider=request.user).order_by('-created_at')

    return render(request, 'services/provider-services.html', {
        'form': form,
        'services': services,
        'editing_service': service_obj,
    })


@login_required
def delete_provider_service(request, service_id):
    if request.user.role != 'provider':
        return redirect('home')
    if not request.user.is_active:
        logout(request)
        return redirect('home')

    service_obj = get_object_or_404(Service, id=service_id, provider=request.user)
    service_obj.delete()
    return redirect('provider_services')


@login_required
def create_booking(request, service_id):
    service_obj = get_object_or_404(
        Service,
        id=service_id,
        provider__is_active=True,
        provider__provider_status='approved',
    )
    provider = service_obj.provider

    if request.user == provider:
        return HttpResponse('You cannot book yourself.')

    if not provider.is_active or provider.provider_status != 'approved':
        return HttpResponse('Provider is unavailable right now.')

    if request.method == 'POST':
        date = request.POST.get('date')
        time = request.POST.get('time')
        address = request.POST.get('address', '').strip()
        use_live_location = request.POST.get('use_live_location') == '1'
        lat_raw = request.POST.get('latitude', '').strip()
        lng_raw = request.POST.get('longitude', '').strip()

        lat_value = None
        lng_value = None

        if lat_raw and lng_raw:
            try:
                lat_value = Decimal(lat_raw)
                lng_value = Decimal(lng_raw)
                if not _is_india_coordinate(lat_value, lng_value):
                    lat_value = None
                    lng_value = None
            except InvalidOperation:
                lat_value = None
                lng_value = None

        try:
            booking_datetime = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')
        except (TypeError, ValueError):
            return redirect(f"{reverse('service_detail', kwargs={'service_id': service_obj.id})}?booking_error=invalid_datetime")

        if timezone.is_naive(booking_datetime):
            booking_datetime = timezone.make_aware(booking_datetime, timezone.get_current_timezone())

        if booking_datetime.date() < timezone.localdate():
            return redirect(f"{reverse('service_detail', kwargs={'service_id': service_obj.id})}?booking_error=past_date")

        available_window = _parse_available_window(service_obj.available_time)
        has_available_time = bool((service_obj.available_time or '').strip())
        if has_available_time and not available_window:
            return redirect(f"{reverse('service_detail', kwargs={'service_id': service_obj.id})}?booking_error=unavailable_time")
        if available_window:
            booking_time = booking_datetime.time()
            if not _is_time_in_window(booking_time, available_window[0], available_window[1]):
                return redirect(f"{reverse('service_detail', kwargs={'service_id': service_obj.id})}?booking_error=unavailable_time")

        booking = Booking.objects.create(
            user=request.user,
            provider=provider,
            service=service_obj,
            service_name=service_obj.name,
            date=booking_datetime,
            amount=service_obj.price,
            service_address=address,
            use_live_location=use_live_location,
            latitude=lat_value,
            longitude=lng_value,
            status='pending',
            payment_status='pending',
        )

        customer_name = request.user.first_name or request.user.username
        location_text = address or 'No address provided'
        if lat_value is not None and lng_value is not None:
            location_text += f' (live: {lat_value}, {lng_value})'

        Notification.objects.create(
            provider=provider,
            booking=booking,
            message=f'New booking from {customer_name} for {service_obj.name}. Location: {location_text}'
        )

        return redirect('booking_status', booking_id=booking.id)

    return redirect('service_detail', service_id=service_obj.id)
