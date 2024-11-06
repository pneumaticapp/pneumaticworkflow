# Generated by Django 2.2 on 2023-05-26 09:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_subscription', models.BooleanField()),
                ('name', models.CharField(max_length=500)),
                ('is_active', models.BooleanField()),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='Price',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=500)),
                ('code', models.CharField(max_length=100)),
                ('stripe_id', models.CharField(max_length=250, unique=True)),
                ('trial_days', models.PositiveIntegerField(null=True)),
                ('min_quantity', models.PositiveIntegerField(default=1)),
                ('max_quantity', models.PositiveIntegerField()),
                ('price_type', models.CharField(choices=[('one_time', 'one_time'), ('recurring', 'recurring')], max_length=50)),
                ('price', models.PositiveIntegerField(help_text='in cents')),
                ('billing_period', models.CharField(choices=[('daily', 'daily'), ('weekly', 'weekly'), ('monthly', 'monthly'), ('yearly', 'yearly')], help_text='For "one time" price type only', max_length=100)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payment.Product')),
            ],
            options={
                'ordering': ('product_id', 'id'),
            },
        ),
    ]