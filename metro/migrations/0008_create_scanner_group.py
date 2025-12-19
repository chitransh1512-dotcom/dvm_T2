from django.db import migrations

def create_scanner_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="Scanner")

class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("metro", "0007_alter_ticket_owner"),
    ]

    operations = [
        migrations.RunPython(create_scanner_group),
    ]
