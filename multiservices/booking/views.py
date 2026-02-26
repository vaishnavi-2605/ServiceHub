import random
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse

from notifications.models import Notification
from accounts.models import CustomUser
from .models import Booking, BookingReport


# Create your views here.

def _is_provider_allowed(user):
    return user.role == 'provider' and user.is_active and user.provider_status == 'approved'

@login_required
def booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # for security
    if request.user.role == 'provider' and not _is_provider_allowed(request.user):
        logout(request)
        return redirect('home')

    if request.user != booking.user and request.user != booking.provider:
        return redirect('home')

    if request.user == booking.user and booking.status == 'rejected':
        return redirect('user_dashboard')

    user_map_url = None
    provider_map_url = None
    hide_user_location_for_provider = (
        request.user == booking.provider
        and (booking.provider_marked_done or booking.status == 'completed')
    )

    if (
        booking.latitude is not None
        and booking.longitude is not None
        and not hide_user_location_for_provider
    ):
        user_map_url = f"https://maps.google.com/?q={booking.latitude},{booking.longitude}"

    if booking.provider_latitude is not None and booking.provider_longitude is not None:
        provider_map_url = f"https://maps.google.com/?q={booking.provider_latitude},{booking.provider_longitude}"

    latest_notification = (
        Notification.objects.filter(user=request.user)
        | Notification.objects.filter(provider=request.user)
    ).order_by('-id').first()

    existing_report = None
    if request.user == booking.user:
        existing_report = BookingReport.objects.filter(booking=booking, user=request.user).first()

    return render(request, 'booking/booking-status.html', {
        'booking': booking,
        'user_map_url': user_map_url,
        'provider_map_url': provider_map_url,
        'is_provider': request.user == booking.provider,
        'is_user': request.user == booking.user,
        'latest_notification_id': latest_notification.id if latest_notification else 0,
        'existing_report': existing_report,
    })


@login_required
def update_live_location(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.user:
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method_not_allowed'}, status=405)

    lat_raw = request.POST.get('latitude', '').strip()
    lng_raw = request.POST.get('longitude', '').strip()

    try:
        lat_value = Decimal(lat_raw)
        lng_value = Decimal(lng_raw)
    except (InvalidOperation, ValueError):
        return JsonResponse({'ok': False, 'error': 'invalid_coordinates'}, status=400)

    booking.use_live_location = True
    booking.latitude = lat_value
    booking.longitude = lng_value
    booking.save(update_fields=['use_live_location', 'latitude', 'longitude'])

    return JsonResponse({'ok': True, 'latitude': str(lat_value), 'longitude': str(lng_value)})


@login_required
def update_provider_live_location(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user.role == 'provider' and not _is_provider_allowed(request.user):
        logout(request)
        return JsonResponse({'ok': False, 'error': 'inactive_provider'}, status=403)

    if request.user != booking.provider:
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'method_not_allowed'}, status=405)

    lat_raw = request.POST.get('latitude', '').strip()
    lng_raw = request.POST.get('longitude', '').strip()

    try:
        lat_value = Decimal(lat_raw)
        lng_value = Decimal(lng_raw)
    except (InvalidOperation, ValueError):
        return JsonResponse({'ok': False, 'error': 'invalid_coordinates'}, status=400)

    booking.provider_latitude = lat_value
    booking.provider_longitude = lng_value
    booking.save(update_fields=['provider_latitude', 'provider_longitude'])

    return JsonResponse({'ok': True, 'latitude': str(lat_value), 'longitude': str(lng_value)})


@login_required
def live_location_data(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.user and request.user != booking.provider:
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

    hide_user_location_for_provider = (
        request.user == booking.provider
        and (booking.provider_marked_done or booking.status == 'completed')
    )

    user_latitude = None if hide_user_location_for_provider else (
        str(booking.latitude) if booking.latitude is not None else None
    )
    user_longitude = None if hide_user_location_for_provider else (
        str(booking.longitude) if booking.longitude is not None else None
    )

    return JsonResponse({
        'ok': True,
        'latitude': user_latitude,
        'longitude': user_longitude,
        'provider_latitude': str(booking.provider_latitude) if booking.provider_latitude is not None else None,
        'provider_longitude': str(booking.provider_longitude) if booking.provider_longitude is not None else None,
        'use_live_location': booking.use_live_location,
        'status': booking.status,
    })


@login_required
def start_service(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user.role == 'provider' and not _is_provider_allowed(request.user):
        logout(request)
        return redirect('home')

    if request.user != booking.provider:
        return redirect('home')

    if request.method == 'POST' and booking.status == 'accepted':
        entered_otp = request.POST.get('otp', '').strip()

        if entered_otp == (booking.otp or ''):
            booking.status = 'in_progress'
            booking.save()

            Notification.objects.create(
                user=booking.user,
                booking=booking,
                message=f'Provider accepted OTP for booking #{booking.id}. Work in progress.'
            )
            return redirect(f"{reverse('booking_status', kwargs={'booking_id': booking.id})}?otp=accepted")
        return redirect(f"{reverse('booking_status', kwargs={'booking_id': booking.id})}?otp=invalid")

    return redirect('booking_status', booking_id=booking.id)


@login_required
def mark_done(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user.role == 'provider' and not _is_provider_allowed(request.user):
        logout(request)
        return redirect('home')

    if request.user != booking.provider:
        return redirect('home')

    if request.method == 'POST' and booking.status == 'in_progress':
        booking.provider_marked_done = True
        booking.save(update_fields=['provider_marked_done'])

        Notification.objects.create(
            user=booking.user,
            booking=booking,
            message=f'Provider marked booking #{booking.id} as done. Please complete payment.'
        )

    return redirect('booking_status', booking_id=booking.id)


@login_required
def confirm_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.user:
        return redirect('home')

    if request.method == 'POST' and booking.status == 'in_progress' and booking.provider_marked_done:
        payment_mode = request.POST.get('payment_mode', '').strip()
        if payment_mode in ['cash', 'online']:
            booking.payment_mode = payment_mode
            booking.payment_status = 'paid'
            booking.status = 'completed'
            booking.save(update_fields=['payment_mode', 'payment_status', 'status'])

            Notification.objects.create(
                provider=booking.provider,
                booking=booking,
                message=f'User completed {payment_mode} payment for booking #{booking.id}.'
            )

    return redirect('booking_status', booking_id=booking.id)


@login_required
def submit_feedback(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.user:
        return redirect('home')

    if request.method == 'POST' and booking.status == 'completed' and booking.payment_status == 'paid':
        rating = request.POST.get('rating', '').strip()
        feedback_text = request.POST.get('feedback_text', '').strip()

        try:
            rating_value = int(rating)
        except ValueError:
            rating_value = None

        if rating_value and 1 <= rating_value <= 5:
            booking.feedback_rating = rating_value
            booking.feedback_text = feedback_text
            booking.save(update_fields=['feedback_rating', 'feedback_text'])

            Notification.objects.create(
                provider=booking.provider,
                booking=booking,
                message=f'You received {rating_value}/5 feedback for booking #{booking.id}.'
            )

    return redirect('booking_status', booking_id=booking.id)


@login_required
def accept_booking(request, booking_id):
    if request.user.role == 'provider' and not _is_provider_allowed(request.user):
        logout(request)
        return redirect('home')

    booking = get_object_or_404(Booking, id=booking_id, provider=request.user)
    booking.status = 'accepted'
    booking.otp = str(random.randint(1000, 9999))
    booking.save()

    Notification.objects.filter(provider=request.user, booking=booking).update(is_read=True)
    Notification.objects.create(
        user=booking.user,
        booking=booking,
        message=f'Your booking #{booking.id} was accepted by {request.user.first_name or request.user.username}. OTP: {booking.otp}'
    )

    return redirect('booking_status', booking_id=booking.id)


@login_required
def submit_report(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.user:
        return redirect('home')

    if request.method != 'POST':
        return redirect('booking_status', booking_id=booking.id)

    reason = request.POST.get('reason', '').strip()
    details = request.POST.get('details', '').strip()

    if not reason:
        return redirect(f"{reverse('booking_status', kwargs={'booking_id': booking.id})}?report_error=1")

    report, created = BookingReport.objects.get_or_create(
        booking=booking,
        user=request.user,
        defaults={
            'provider': booking.provider,
            'reason': reason[:120],
            'details': details,
        },
    )

    if not created:
        report.reason = reason[:120]
        report.details = details
        report.is_reviewed = False
        report.save(update_fields=['reason', 'details', 'is_reviewed'])

    reporter_name = request.user.first_name or request.user.username
    provider_name = booking.provider.first_name or booking.provider.username
    admin_users = CustomUser.objects.filter(is_superuser=True)
    for admin_user in admin_users:
        Notification.objects.create(
            user=admin_user,
            booking=booking,
            message=f'Report received for provider {provider_name} on booking #{booking.id} by {reporter_name}.',
        )

    return redirect(f"{reverse('booking_status', kwargs={'booking_id': booking.id})}?reported=1")


@login_required
def reject_booking(request, booking_id):
    if request.user.role == 'provider' and not _is_provider_allowed(request.user):
        logout(request)
        return redirect('home')

    booking = get_object_or_404(Booking, id=booking_id, provider=request.user)
    if booking.status == 'completed' or booking.payment_status == 'paid':
        return redirect('provider_dashboard')
    if booking.status == 'rejected':
        return redirect('provider_dashboard')

    booking.status = 'rejected'
    booking.save()

    Notification.objects.filter(provider=request.user, booking=booking).update(is_read=True)
    Notification.objects.create(
        user=booking.user,
        booking=booking,
        message=f'Your booking #{booking.id} was rejected by {request.user.first_name or request.user.username}.'
    )

    return redirect('provider_dashboard')


@login_required
def user_reject_booking(request, booking_id):
    if request.user.role != 'user':
        return redirect('home')
    if request.method != 'POST':
        return redirect('booking_status', booking_id=booking_id)

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status != 'pending':
        return redirect('booking_status', booking_id=booking.id)

    booking.status = 'rejected'
    booking.save(update_fields=['status'])

    Notification.objects.create(
        provider=booking.provider,
        booking=booking,
        message=f'User cancelled booking #{booking.id} before provider acceptance.'
    )

    return redirect('user_dashboard')

