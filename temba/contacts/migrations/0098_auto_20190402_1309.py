# Generated by Django 2.1.7 on 2019-04-02 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("contacts", "0097_replace_index")]

    operations = [
        migrations.AlterField(
            model_name="contactfield",
            name="show_in_table",
            field=models.BooleanField(default=False, help_text="Featured field", verbose_name="Shown in Tables"),
        )
    ]