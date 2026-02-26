from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.cache import never_cache

from booking.models import Booking, BookingReport
from notifications.models import Notification
from services.models import Service
from services.constants import normalize_category_name

from .forms import ProviderProfileForm, SignupForm, UserProfileForm
from .models import CustomUser, ProviderProfile


def _redirect_dashboard_for_role(user):
    if user.is_superuser:
        return redirect('admin_dashboard')
    if user.role == 'provider':
        return redirect('provider_dashboard')
    if user.role == 'user':
        return redirect('user_dashboard')
    return redirect('home')


def _apply_history_range(bookings_qs, range_key):
    now = timezone.now()
    if range_key == 'today':
        return bookings_qs.filter(date__date=now.date())
    if range_key == 'week':
        return bookings_qs.filter(date__gte=now - timedelta(days=7))
    if range_key == 'month':
        return bookings_qs.filter(date__gte=now - timedelta(days=30))
    return bookings_qs


def _ensure_active_provider(request):
    if request.user.role == 'provider' and not request.user.is_active:
        logout(request)
        return redirect('home')
    return None


# def hello(request):
#     return HttpResponse('Hello, and welcome to the accounts app!')


def signin(request):
    if request.user.is_authenticated:
        return _redirect_dashboard_for_role(request.user)

    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        username = username_input
        if '@' in username_input:
            user_obj = CustomUser.objects.filter(email__iexact=username_input).first()
            if user_obj:
                username = user_obj.username

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            if user.role == 'provider':
                return redirect('provider_dashboard')
            return redirect('user_dashboard')

        return render(request, 'accounts/signin.html', {
            'error': 'Invalid username or password'
        })

    return render(request, 'accounts/signin.html')


def signup(request):
    if request.user.is_authenticated:
        return _redirect_dashboard_for_role(request.user)

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data.get('role')
            certificate = request.FILES.get('certificate')
            profile_image = request.FILES.get('provider_image')
            aadhaar_card = request.FILES.get('aadhaar_card')

            if role == 'provider':
                missing_docs = []
                if not profile_image:
                    missing_docs.append('Provider profile image is required.')
                if not certificate:
                    missing_docs.append('Certificate upload is required.')
                if not aadhaar_card:
                    missing_docs.append('Aadhaar card upload is required.')
                if missing_docs:
                    form.add_error(None, ' '.join(missing_docs))
                    return render(request, 'accounts/signup.html', {'form': form})

            user = form.save()

            if user.role == 'provider':
                user.provider_status = 'pending'
                user.is_active = True
                user.save(update_fields=['provider_status', 'is_active'])
                category_raw = request.POST.get('category', '').strip()
                category_other = request.POST.get('category_other', '').strip()
                if category_raw == 'Other' and category_other:
                    category_raw = category_other
                category = normalize_category_name(category_raw) or 'General Service'
                exp_raw = request.POST.get('experience', '0').strip()
                service_time = request.POST.get('service_time', '').strip()
                price_raw = request.POST.get('service_price', '').strip()
                provider_phone = request.POST.get('provider_phone', '').strip() or user.mobile_no
                provider_address = request.POST.get('provider_address', '').strip() or user.address

                try:
                    experience = int(exp_raw) if exp_raw else 0
                except ValueError:
                    experience = 0
                try:
                    price_value = float(price_raw) if price_raw else 500
                except ValueError:
                    price_value = 500

                profile, created = ProviderProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone': provider_phone,
                        'address': provider_address,
                        'experience': experience,
                        'bio': f'Provider for {category} services.',
                    },
                )

                if not created:
                    profile.phone = provider_phone
                    profile.address = provider_address
                    profile.experience = experience

                if certificate:
                    profile.certificate = certificate

                if profile_image:
                    profile.profile_image = profile_image
                if aadhaar_card:
                    profile.aadhaar_card = aadhaar_card

                profile.save()

                Service.objects.get_or_create(
                    provider=user,
                    name=category,
                    defaults={
                        'description': f'Professional {category} service.',
                        'price': price_value,
                        'available_time': service_time,
                        'available_days': '',
                    },
                )

            login(request, user)

            if user.role == 'provider':
                return redirect('provider_dashboard')
            return redirect('home')
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


@login_required
@never_cache
def signout(request):
    logout(request)
    return redirect('home')


@login_required
@never_cache
def user_dashboard(request):
    if request.user.role != 'user':
        return _redirect_dashboard_for_role(request.user)

    history_range = request.GET.get('history_range', 'all').strip()
    if history_range not in ['all', 'today', 'week', 'month']:
        history_range = 'all'

    bookings = Booking.objects.filter(user=request.user).select_related('provider', 'service').order_by('-created_at')
    history_bookings = bookings.filter(status__in=['completed', 'rejected'])
    history_bookings = _apply_history_range(history_bookings, history_range)
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    latest_notification = Notification.objects.filter(user=request.user).order_by('-id').first()

    total = bookings.count()
    active = bookings.exclude(status='completed').count()
    completed = bookings.filter(status='completed').count()

    provider_ids = [b.provider_id for b in bookings]
    profiles = ProviderProfile.objects.filter(user_id__in=provider_ids)
    profile_map = {p.user_id: p for p in profiles}

    for b in bookings:
        profile = profile_map.get(b.provider_id)
        b.provider_address = profile.address if profile else ''

    user_service_history = (
        _apply_history_range(Booking.objects.filter(user=request.user), history_range)
        .values('service_name')
        .annotate(total=Count('id'))
        .order_by('-total', 'service_name')[:10]
    )

    return render(request, 'accounts/user-dashboard.html', {
        'bookings': bookings,
        'history_bookings': history_bookings,
        'user_service_history': user_service_history,
        'history_range': history_range,
        'notifications': notifications,
        'latest_notification_id': latest_notification.id if latest_notification else 0,
        'total_bookings': total,
        'active_bookings': active,
        'completed_bookings': completed,
    })


@login_required
@never_cache
def provider_dashboard(request):
    if request.user.role != 'provider':
        return _redirect_dashboard_for_role(request.user)
    guard = _ensure_active_provider(request)
    if guard:
        return guard

    history_range = request.GET.get('history_range', 'all').strip()
    if history_range not in ['all', 'today', 'week', 'month']:
        history_range = 'all'

    provider_is_approved = request.user.provider_status == 'approved'
    profile, _ = ProviderProfile.objects.get_or_create(
        user=request.user,
        defaults={'phone': request.user.mobile_no, 'address': request.user.address, 'experience': 0, 'bio': ''},
    )
    provider_services = Service.objects.filter(provider=request.user).order_by('-created_at')

    if not provider_is_approved:
        return render(request, 'accounts/provider-dashboard.html', {
            'pending_bookings': [],
            'active_bookings': [],
            'completed_bookings': [],
            'history_bookings': [],
            'provider_service_history': [],
            'provider_services': provider_services,
            'history_range': history_range,
            'notifications': [],
            'latest_notification_id': 0,
            'profile': profile,
            'total_bookings': 0,
            'provider_earnings': 0,
            'provider_is_approved': False,
        })

    pending = Booking.objects.filter(
        provider=request.user,
        status='pending'
    ).select_related('user', 'service').order_by('-created_at')

    active = Booking.objects.filter(
        provider=request.user,
        status__in=['accepted', 'in_progress']
    ).select_related('user', 'service').order_by('-created_at')

    completed = Booking.objects.filter(
        provider=request.user,
        status='completed'
    ).select_related('user', 'service').order_by('-created_at')
    history_bookings = Booking.objects.filter(
        provider=request.user,
        status__in=['completed', 'rejected']
    ).select_related('user', 'service').order_by('-created_at')
    history_bookings = _apply_history_range(history_bookings, history_range)

    notifications = Notification.objects.filter(
        provider=request.user,
        is_read=False
    ).order_by('-created_at')
    latest_notification = Notification.objects.filter(provider=request.user).order_by('-id').first()

    total_bookings = pending.count() + active.count() + completed.count()
    earnings = completed.aggregate(total=Sum('amount'))['total'] or 0
    provider_service_history = (
        _apply_history_range(Booking.objects.filter(provider=request.user), history_range)
        .values('service_name')
        .annotate(total=Count('id'))
        .order_by('-total', 'service_name')[:10]
    )
    return render(request, 'accounts/provider-dashboard.html', {
        'pending_bookings': pending,
        'active_bookings': active,
        'completed_bookings': completed,
        'history_bookings': history_bookings,
        'provider_service_history': provider_service_history,
        'provider_services': provider_services,
        'history_range': history_range,
        'notifications': notifications,
        'latest_notification_id': latest_notification.id if latest_notification else 0,
        'profile': profile,
        'total_bookings': total_bookings,
        'provider_earnings': earnings,
        'provider_is_approved': True,
    })

@login_required
@never_cache
def admin_dashboard(request):
    if not request.user.is_superuser:
        return _redirect_dashboard_for_role(request.user)

    providers_qs = CustomUser.objects.filter(role='provider').annotate(
        service_count=Count('services', distinct=True),
        booking_count=Count('provider_bookings', distinct=True),
        completed_booking_count=Count(
            'provider_bookings',
            filter=Q(provider_bookings__status='completed'),
            distinct=True,
        ),
        revenue=Sum(
            'provider_bookings__amount',
            filter=Q(
                provider_bookings__status='completed',
                provider_bookings__payment_status='paid',
            ),
        ),
        avg_rating=Avg('provider_bookings__feedback_rating'),
    ).order_by('-booking_count', 'username')

    provider_ids = [provider.id for provider in providers_qs]
    profile_map = {
        profile.user_id: profile
        for profile in ProviderProfile.objects.filter(user_id__in=provider_ids)
    }
    for provider in providers_qs:
        provider.profile = profile_map.get(provider.id)

    services_qs = Service.objects.select_related('provider').annotate(
        booking_count=Count('bookings', distinct=True),
        completed_count=Count('bookings', filter=Q(bookings__status='completed'), distinct=True),
        total_revenue=Sum(
            'bookings__amount',
            filter=Q(
                bookings__status='completed',
                bookings__payment_status='paid',
            ),
        ),
        avg_rating=Avg('bookings__feedback_rating'),
    ).order_by('-booking_count', '-price', 'name')

    top_provider = providers_qs.first()
    top_booked_service = services_qs.first()
    top_priced_service = Service.objects.select_related('provider').order_by('-price', 'name').first()
    top_revenue_service = (
        Service.objects.select_related('provider')
        .annotate(
            revenue=Sum(
                'bookings__amount',
                filter=Q(bookings__status='completed', bookings__payment_status='paid'),
            )
        )
        .order_by('-revenue', '-price', 'name')
        .first()
    )

    total_providers = CustomUser.objects.filter(role='provider').count()
    total_services = Service.objects.count()
    total_bookings = Booking.objects.count()
    completed_bookings = Booking.objects.filter(status='completed').count()
    total_revenue = (
        Booking.objects.filter(status='completed', payment_status='paid').aggregate(total=Sum('amount'))['total'] or 0
    )
    # Keep math Decimal-safe; total_revenue can be Decimal from aggregation.
    monthly_target = max(100000, int((total_revenue * 12) / 10))
    target_progress = int(min((total_revenue / monthly_target) * 100, 100)) if monthly_target else 0
    target_remaining = max(monthly_target - int(total_revenue), 0)

    chart_services = list(services_qs[:7])
    max_chart_bookings = max((service.booking_count or 0 for service in chart_services), default=0)
    if total_bookings == 0 and chart_services:
        for service in chart_services:
            service.chart_height = 100
    else:
        if max_chart_bookings == 0:
            max_chart_bookings = 1
        for service in chart_services:
            service.chart_height = int(((service.booking_count or 0) / max_chart_bookings) * 100)

    recent_reports = BookingReport.objects.select_related('booking', 'user', 'provider').order_by('-created_at')[:15]
    top_services = list(services_qs[:5])
    latest_bookings = list(
        Booking.objects.select_related('user', 'provider', 'service').order_by('-created_at')[:6]
    )

    return render(request, 'accounts/admin-dashboard.html', {
        'providers': providers_qs,
        'services': services_qs[:50],
        'total_providers': total_providers,
        'total_services': total_services,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'total_revenue': total_revenue,
        'top_provider': top_provider,
        'top_booked_service': top_booked_service,
        'top_priced_service': top_priced_service,
        'top_revenue_service': top_revenue_service,
        'chart_services': chart_services,
        'max_chart_bookings': max_chart_bookings,
        'monthly_target': monthly_target,
        'target_progress': target_progress,
        'target_remaining': target_remaining,
        'recent_reports': recent_reports,
        'top_services': top_services,
        'latest_bookings': latest_bookings,
    })


@login_required
def admin_remove_provider(request, provider_id):
    if not request.user.is_superuser:
        return _redirect_dashboard_for_role(request.user)
    if request.method != 'POST':
        return redirect('admin_dashboard')

    provider = get_object_or_404(CustomUser, id=provider_id, role='provider')
    if provider.is_active or provider.provider_status != 'rejected':
        provider.is_active = False
        provider.provider_status = 'rejected'
        provider.save(update_fields=['is_active', 'provider_status'])

    return redirect(f"{reverse('admin_dashboard')}?removed=1")


@login_required
def admin_approve_provider(request, provider_id):
    if not request.user.is_superuser:
        return _redirect_dashboard_for_role(request.user)
    if request.method != 'POST':
        return redirect('admin_dashboard')

    provider = get_object_or_404(CustomUser, id=provider_id, role='provider')
    provider.provider_status = 'approved'
    provider.is_active = True
    provider.save(update_fields=['provider_status', 'is_active'])
    return redirect(f"{reverse('admin_dashboard')}?approved=1")


@login_required
@never_cache
def admin_provider_detail(request, provider_id):
    if not request.user.is_superuser:
        return _redirect_dashboard_for_role(request.user)

    provider = get_object_or_404(CustomUser, id=provider_id, role='provider')
    profile = ProviderProfile.objects.filter(user=provider).first()
    provider_services = Service.objects.filter(provider=provider).order_by('-created_at')
    provider_bookings = (
        Booking.objects.filter(provider=provider)
        .select_related('user', 'service')
        .order_by('-created_at')[:100]
    )

    return render(request, 'accounts/admin-provider-detail.html', {
        'provider': provider,
        'profile': profile,
        'provider_services': provider_services,
        'provider_bookings': provider_bookings,
    })


@login_required
@never_cache
def admin_report_detail(request, report_id):
    if not request.user.is_superuser:
        return _redirect_dashboard_for_role(request.user)

    report = get_object_or_404(
        BookingReport.objects.select_related('booking', 'user', 'provider'),
        id=report_id,
    )
    report.is_reviewed = True
    report.save(update_fields=['is_reviewed'])

    provider = report.provider
    profile = ProviderProfile.objects.filter(user=provider).first()
    provider_bookings = (
        Booking.objects.filter(provider=provider)
        .select_related('user', 'service')
        .order_by('-created_at')[:50]
    )

    return render(request, 'accounts/admin-report-detail.html', {
        'report': report,
        'provider': provider,
        'profile': profile,
        'provider_bookings': provider_bookings,
    })

@login_required
@never_cache
def update_profile(request):
    guard = _ensure_active_provider(request)
    if guard:
        return guard
    provider_form = None
    profile = None

    if request.user.role == 'provider':
        profile, _ = ProviderProfile.objects.get_or_create(
            user=request.user,
            defaults={'phone': request.user.mobile_no, 'address': request.user.address, 'experience': 0, 'bio': ''},
        )

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=request.user, prefix='user')
        if request.user.role == 'provider':
            provider_form = ProviderProfileForm(request.POST, request.FILES, instance=profile, prefix='provider')
            if user_form.is_valid() and provider_form.is_valid():
                user_form.save()
                provider_form.save()
                return redirect(f"{reverse('provider_dashboard')}?updated=1")
        else:
            if user_form.is_valid():
                user_form.save()
                return redirect(f"{reverse('user_dashboard')}?updated=1")
    else:
        user_form = UserProfileForm(instance=request.user, prefix='user')
        if request.user.role == 'provider':
            provider_form = ProviderProfileForm(instance=profile, prefix='provider')

    return render(request, 'accounts/update_profile.html', {
        'user_form': user_form,
        'provider_form': provider_form,
        'is_provider': request.user.role == 'provider',
    })


