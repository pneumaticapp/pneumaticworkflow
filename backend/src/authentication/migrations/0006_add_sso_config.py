# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0005_auto_20231025_2121'),
    ]

    operations = [
        migrations.CreateModel(
            name='SSOConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[('auth0', 'Auth0'), ('okta', 'Okta')], max_length=50, verbose_name='SSO Provider')),
                ('domain', models.CharField(max_length=255)),
                ('client_id', models.CharField(max_length=255)),
                ('client_secret', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sso_configurations', to='accounts.Account')),
            ],
            options={
                'ordering': ['account', 'provider'],
            },
        ),
        migrations.AddConstraint(
            model_name='ssoconfig',
            constraint=models.UniqueConstraint(condition=models.Q(is_active=True), fields=('account',), name='unique_active_sso_per_account'),
        ),
        migrations.AlterUniqueTogether(
            name='ssoconfig',
            unique_together={('account', 'provider')},
        ),
    ]
