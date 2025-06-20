# Generated by Django 5.0.2 on 2025-06-18 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_adminreport_report_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminreport',
            name='admin_management_area',
            field=models.CharField(blank=True, choices=[('deposits', 'Deposits'), ('investment_tiers', 'Investment Tiers'), ('investments', 'Investments'), ('users', 'Users'), ('wallets', 'Wallets'), ('withdrawals', 'Withdrawals'), ('referrals', 'Referrals'), ('daily_specials', 'Daily Specials'), ('vouchers', 'Vouchers'), ('ip_addresses', 'IP Addresses')], max_length=50),
        ),
    ]
