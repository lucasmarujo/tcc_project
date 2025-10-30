"""Script rápido para criar um aluno."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from students.models import Student

# Criar aluno com matrícula 123
student, created = Student.objects.get_or_create(
    registration_number='123',
    defaults={
        'name': 'Aluno Teste',
        'email': 'teste@aluno.br',
        'is_active': True
    }
)

if created:
    print(f"[OK] Aluno criado com sucesso!")
    print(f"  Matricula: {student.registration_number}")
    print(f"  Nome: {student.name}")
    print(f"  Email: {student.email}")
    print(f"  API Key: {student.api_key}")
else:
    print(f"[OK] Aluno ja existe!")
    print(f"  Matricula: {student.registration_number}")
    print(f"  Nome: {student.name}")

