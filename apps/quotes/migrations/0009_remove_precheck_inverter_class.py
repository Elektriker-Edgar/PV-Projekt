from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0008_precheck_wallbox_precheck_wallbox_cable_length_m_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='precheck',
            name='inverter_class',
        ),
    ]
