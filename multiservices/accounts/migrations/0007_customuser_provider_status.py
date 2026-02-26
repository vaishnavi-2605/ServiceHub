from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_delete_passwordresetotp'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='provider_status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                default='approved',
                max_length=20,
            ),
        ),
    ]
