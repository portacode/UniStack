from django.db import migrations


def preserve_legacy_request_columns(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        columns = {
            column.name
            for column in connection.introspection.get_table_description(
                cursor, "unicom_request"
            )
        }
        if "failure_kind" in columns:
            cursor.execute("ALTER TABLE unicom_request ALTER COLUMN failure_kind SET DEFAULT ''")
        if "retry_count" in columns:
            cursor.execute("ALTER TABLE unicom_request ALTER COLUMN retry_count SET DEFAULT 0")


class Migration(migrations.Migration):
    initial = True
    dependencies = [("unicom", "0026_message_email_sender_authenticated")]
    operations = [
        migrations.RunPython(preserve_legacy_request_columns, migrations.RunPython.noop)
    ]
