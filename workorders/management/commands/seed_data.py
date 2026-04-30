from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from workorders.models import WorkOrder, Brigade, BrigadeMember
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Создать демо-данные'

    def handle(self, *args, **kwargs):

        # Группы
        groups = ['Руководитель', 'Старший наряда', 'Работник']
        for name in groups:
            Group.objects.get_or_create(name=name)
        self.stdout.write('✅ Группы созданы')

        # Пользователи
        boss, _ = User.objects.get_or_create(username='boss')
        boss.set_password('йцук1234')
        boss.first_name = 'Руководитель'
        boss.last_name = 'Наряда'
        boss.position = 'Начальник цеха'
        boss.save()
        boss.groups.set([Group.objects.get(name='Руководитель')])

        senior, _ = User.objects.get_or_create(username='senior')
        senior.set_password('йцук1234')
        senior.first_name = 'Старший'
        senior.last_name = 'Наряда'
        senior.position = 'Бригадир'
        senior.save()
        senior.groups.set([Group.objects.get(name='Старший наряда')])

        worker1, _ = User.objects.get_or_create(username='worker1')
        worker1.set_password('йцук1234')
        worker1.first_name = 'Рабочий'
        worker1.last_name = 'Первый'
        worker1.position = 'Электрослесарь'
        worker1.save()
        worker1.groups.set([Group.objects.get(name='Работник')])

        worker2, _ = User.objects.get_or_create(username='worker2')
        worker2.set_password('йцук1234')
        worker2.first_name = 'Рабочий'
        worker2.last_name = 'Второй'
        worker2.position = 'Слесарь'
        worker2.save()
        worker2.groups.set([Group.objects.get(name='Работник')])

        self.stdout.write('✅ Пользователи созданы')

        # Тестовый наряд
        if not WorkOrder.objects.filter(title='Ремонт конвейера №1').exists():
            wo = WorkOrder.objects.create(
                title='Ремонт конвейера №1',
                date=date.today() + timedelta(days=1),
                location='Цех №1, участок ДО',
                position='Начальник цеха',
                work_type='Плановый ремонт конвейерной ленты',
                instructions='Соблюдать правила техники безопасности. Работать в защитных очках.',
                issuer=boss,
                assigned_to=senior,
            )
            brigade = Brigade.objects.create(
                name=f'Бригада — {wo.title}',
                work_order=wo
            )
            BrigadeMember.objects.create(brigade=brigade, user=senior, is_leader=True)
            BrigadeMember.objects.create(brigade=brigade, user=worker1, is_leader=False)
            BrigadeMember.objects.create(brigade=brigade, user=worker2, is_leader=False)
            self.stdout.write('✅ Тестовый наряд создан')

        self.stdout.write(self.style.SUCCESS('''
=============================
Демо-данные готовы!

Логины:
  boss    / йцук1234  (Руководитель)
  senior  / йцук1234  (Старший наряда)
  worker1 / йцук1234  (Работник)
  worker2 / йцук1234  (Работник)
=============================
        '''))