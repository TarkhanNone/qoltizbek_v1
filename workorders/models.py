from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class WorkOrder(models.Model):
    STATUS_CHOICES = [
        ('draft',    'Черновик'),
        ('progress', 'В процессе'),
        ('done',     'Завершён'),
        ('closed',   'Закрыт'),
    ]

    title        = models.CharField(max_length=255, verbose_name='Название')
    date         = models.DateField(verbose_name='Дата')
    location     = models.CharField(max_length=255, verbose_name='Место выполнения')
    position     = models.CharField(max_length=255, verbose_name='Должность', blank=True)
    work_type    = models.TextField(verbose_name='Вид работы')
    instructions = models.TextField(verbose_name='Инструкции по ТБ')

    issuer      = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='issued_orders',
        verbose_name='Выдал'
    )
    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='assigned_orders',
        verbose_name='Старший наряда',
        null=True, blank=True
    )

    status     = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='draft', verbose_name='Статус'
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Наряд'
        verbose_name_plural = 'Наряды'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Brigade(models.Model):
    work_order = models.OneToOneField(
        WorkOrder, on_delete=models.CASCADE,
        related_name='brigade',
        verbose_name='Наряд'
    )
    name = models.CharField(max_length=255, verbose_name='Название')

    class Meta:
        verbose_name = 'Бригада'
        verbose_name_plural = 'Бригады'

    def __str__(self):
        return self.name


class BrigadeMember(models.Model):
    brigade    = models.ForeignKey(
        Brigade, on_delete=models.CASCADE,
        related_name='members',
        verbose_name='Бригада'
    )
    user       = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    is_leader  = models.BooleanField(default=False, verbose_name='Старший наряда')

    class Meta:
        verbose_name = 'Член бригады'
        verbose_name_plural = 'Члены бригады'
        unique_together = ('brigade', 'user')

    def __str__(self):
        role = 'Старший' if self.is_leader else 'Работник'
        return f"{self.user} ({role})"


class Signature(models.Model):
    ROLE_CHOICES = [
        ('issuer',  'Выдал'),
        ('leader',  'Старший наряда'),
        ('worker',  'Работник'),
    ]

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE,
        related_name='signatures',
        verbose_name='Наряд'
    )
    user      = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    role      = models.CharField(
        max_length=20, choices=ROLE_CHOICES,
        verbose_name='Роль'
    )
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Подпись'
        verbose_name_plural = 'Подписи'
        unique_together = ('work_order', 'user', 'role')

    def __str__(self):
        return f"{self.user} — {self.get_role_display()}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('update', 'Обновление'),
        ('delete', 'Удаление'),
        ('sign',   'Подписание'),
        ('close',  'Закрытие'),
    ]

    user       = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, verbose_name='Пользователь'
    )
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name='Наряд'
    )
    action      = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Запись аудита'
        verbose_name_plural = 'Журнал аудита'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.action} — {self.work_order}"