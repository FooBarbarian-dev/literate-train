from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION create_operation_tag()
            RETURNS TRIGGER AS $$
            DECLARE new_tag_id INTEGER;
            BEGIN
                INSERT INTO tags (name, color, category, description, is_default, created_by, created_at, updated_at)
                VALUES ('op:' || LOWER(NEW.name), '#3B82F6', 'operation',
                        'Auto-generated tag for operation: ' || NEW.name,
                        FALSE, NEW.created_by, NOW(), NOW())
                RETURNING id INTO new_tag_id;
                NEW.tag_id := new_tag_id;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER trigger_create_operation_tag
                BEFORE INSERT ON operations
                FOR EACH ROW EXECUTE FUNCTION create_operation_tag();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS trigger_create_operation_tag ON operations;
            DROP FUNCTION IF EXISTS create_operation_tag();
            """,
        ),
    ]
