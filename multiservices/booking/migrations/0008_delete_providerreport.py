from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0007_providerreport'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ProviderReport',
        ),
    ]
