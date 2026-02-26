# MultiServices Django Project

Service booking platform built with Django and SQLite.

Roles:
- user
- provider
- admin (Django superuser)

## 1) Project Layout

Workspace:
- `multiservices/` -> Django project root (run Django commands here)
- `servicesenv/` -> local virtual environment

Inside `multiservices/`:
- `multiservices/` -> settings and root URLs
- `accounts/` -> auth, signup/signin, dashboards, profile update
- `services/` -> service listing, filtering, provider service CRUD, booking create
- `booking/` -> booking workflow (OTP start, payment, feedback, live location)
- `notifications/` -> notifications center
- `core/` -> home and shared partials
- `static/` -> CSS
- `media/` -> uploads
- `db.sqlite3` -> SQLite database

## 2) Run Project

From:
`c:\Users\LENOVO\OneDrive\Desktop\Aict_v2\multiservices`

```powershell
..\servicesenv\Scripts\python.exe manage.py migrate
..\servicesenv\Scripts\python.exe runserver
```

Open:
- `http://127.0.0.1:8000/home/`

## 3) Main URL Map

Root URLs:
- Home: `/home/`
- Django admin: `/admin/`
- Accounts: `/accounts/...`
- Services: `/services/...`
- Booking: `/booking/...`
- Notifications: `/notifications/...`

Accounts URLs:
- Sign in: `/accounts/signin/`
- Sign up: `/accounts/signup/`
- Logout: `/accounts/logout/`
- Profile update: `/accounts/profile/`
- User dashboard: `/accounts/user_dashboard/`
- Provider dashboard: `/accounts/provider_dashboard/`
- Admin dashboard: `/accounts/admin_dashboard/`
- Admin approve provider: `/accounts/admin_dashboard/provider/<provider_id>/approve/`
- Admin remove/delete provider: `/accounts/admin_dashboard/provider/<provider_id>/remove/`
- Admin provider detail: `/accounts/admin_dashboard/provider/<provider_id>/`
- User cancel pending booking: `/accounts/user_dashboard/booking/<booking_id>/reject/`
- Provider accept booking: `/accounts/provider_dashboard/booking/<booking_id>/accept/`
- Provider reject booking: `/accounts/provider_dashboard/booking/<booking_id>/reject/`

Services URLs:
- Services list: `/services/`
- Provider service manager: `/services/provider/manage/`
- Service detail: `/services/<service_id>/`
- Create booking: `/services/<service_id>/book/`

Booking URLs:
- Booking status: `/booking/booking/<booking_id>/`
- Start service with OTP: `/booking/booking/<booking_id>/start/`
- Mark done: `/booking/booking/<booking_id>/mark-done/`
- Confirm payment: `/booking/booking/<booking_id>/pay/`
- Submit feedback: `/booking/booking/<booking_id>/feedback/`
- User live location update: `/booking/booking/<booking_id>/live-location/update/`
- Provider live location update: `/booking/booking/<booking_id>/provider-live-location/update/`
- Live location data API: `/booking/booking/<booking_id>/live-location/data/`

Notifications URLs:
- Center: `/notifications/`
- Mark one read: `/notifications/read/<notification_id>/`
- Mark all read: `/notifications/read-all/`

## 4) Current Auth and Signup Behavior

Sign in:
- Signin form asks for username.
- Backend accepts username and also resolves email to username if email is entered.
- Redirects:
  - superuser -> `/admin/`
  - provider -> provider dashboard
  - user -> user dashboard

Sign up:
- Signup requires: full name, username, email, mobile, address, role, password.
- Provider signup also requires uploads:
  - provider profile image
  - certificate
  - Aadhaar card
- Provider signup additionally captures:
  - category, experience, service time, service price
- On successful provider signup, a provider profile is created and a first service is auto-created.
- New provider approval flow:
  - provider account is created with `provider_status = pending`
  - provider can sign in and open provider dashboard
  - provider sees a message that account is not active yet and must wait for admin verification
  - provider services are not shown on public Services page until admin approval

## 5) Booking and Dashboard Flow

Booking status lifecycle:
- `pending` -> provider accepts/rejects
- user can cancel only while status is `pending`
- provider accept generates 4-digit OTP
- `accepted` -> provider starts service with OTP -> `in_progress`
- provider marks done
- user confirms payment (`cash` or `online`) -> `completed`
- user can submit rating/feedback after payment

Rejection rules:
- user can reject/cancel only at `pending`
- provider can reject at `pending` or `accepted`

User dashboard:
- history table for completed/rejected bookings
- Notifications

Provider dashboard:
- If provider is `pending`, dashboard shows only profile/services with a waiting message (no booking operations).
- Pending, active, completed/history bookings
- Notifications
- Earnings and totals
- Service history summary
- Provider service list
- History range filter: `all`, `today`, `week`, `month`
- User location is hidden to provider after provider marks done or booking completes

Admin provider workflow:
- Providers appear in admin overview with status:
  - `Pending`
  - `Active` (approved)
  - `Removed` (rejected/deleted)
- Admin can open pending provider detail, verify docs, and:
  - Approve: sets `provider_status = approved`, provider becomes bookable/visible
  - Delete/Remove: sets `provider_status = rejected` and disables login

## 6) Availability Rules

- Provider availability time is shown on provider detail page.
- Only approved providers are shown in services list and service detail.
- Users can book only approved providers.
- Booking is validated on backend against provider availability:
  - blocked if selected day is outside configured `available_days` (when set)
  - blocked if selected time is outside configured `available_time` (when parseable)
- User sees booking error messages on provider detail page when unavailable.

## 7) Admin Dashboard Notes

- Latest Bookings overview currently shows 6 most recent bookings.

## 8) Theme and UI Notes

- Global header nav is shared using `core/templates/partials/header.html`.
- No custom day/night admin theme script is active.

## 9) Home Categories Behavior

Home (`/home/`) shows default categories:
- Plumber
- Tutor
- Cleaning
- AC Repair
- Carpenter

Also shows extra categories created by providers.
If a category has a service image, that image is used in the card.

## 10) Upload Paths

Configured with `MEDIA_ROOT = BASE_DIR / 'media'`:
- Provider profile image: `media/providers/images/`
- Provider certificate: `media/providers/certificates/`
- Provider Aadhaar card: `media/providers/aadhaar/`
- Service image: `media/services/images/`

## 11) Database and Admin Access

Create superuser:
```powershell
..\servicesenv\Scripts\python.exe manage.py createsuperuser
```

Access:
- Django admin: `http://127.0.0.1:8000/admin/`

SQLite DB:
- `multiservices/db.sqlite3`

## 12) Migrations and Checks

```powershell
..\servicesenv\Scripts\python.exe manage.py makemigrations
..\servicesenv\Scripts\python.exe manage.py migrate
..\servicesenv\Scripts\python.exe manage.py check
```

## 13) Current Development Notes

- `DEBUG=True`
- `EMAIL_BACKEND = django.core.mail.backends.console.EmailBackend`
- Live location features require browser geolocation permission.
- Root URL `/` is not mapped; use `/home/`.
