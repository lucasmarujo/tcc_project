# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentHeartbeat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_heartbeat', models.DateTimeField(auto_now=True, verbose_name='Último Heartbeat')),
                ('machine_name', models.CharField(blank=True, max_length=200, verbose_name='Nome da Máquina')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='Endereço IP')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='heartbeat', to='students.student', verbose_name='Aluno')),
            ],
            options={
                'verbose_name': 'Heartbeat do Aluno',
                'verbose_name_plural': 'Heartbeats dos Alunos',
                'db_table': 'student_heartbeats',
                'ordering': ['-last_heartbeat'],
            },
        ),
    ]

