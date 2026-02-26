from django.db import migrations, models


def remove_electrical_services(apps, schema_editor):
    Service = apps.get_model('services', 'Service')
    User = apps.get_model('accounts', 'CustomUser')

    electrical_services = Service.objects.filter(name__iexact='electrical')
    provider_ids = electrical_services.values_list('provider_id', flat=True).distinct()

    electrical_services.delete()
    User.objects.filter(id__in=provider_ids, role='provider').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_providerprofile_aadhaar_card'),
        ('services', '0005_remove_service_duration_minutes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='available_days',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.RunPython(remove_electrical_services, migrations.RunPython.noop),
    ]
