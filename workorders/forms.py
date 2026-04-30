import re
from django import forms
from django.utils import timezone
from .models import WorkOrder, Brigade, BrigadeMember
from accounts.models import User


class WorkOrderForm(forms.ModelForm):
    senior = forms.ModelChoiceField(
        queryset=User.objects.filter(
            groups__name='Старший наряда'
        ).distinct(),
        label='Старший наряда',
        empty_label='Выберите старшего наряда',
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={'required': 'Выберите старшего наряда'}
    )
    workers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(
            groups__name='Работник'
        ).distinct(),
        label='Работники',
        widget=forms.CheckboxSelectMultiple,
        error_messages={'required': 'Выберите хотя бы одного работника'}
    )

    class Meta:
        model = WorkOrder
        fields = ['title', 'date', 'location', 'position', 'work_type', 'instructions']
        widgets = {
            'title':        forms.TextInput(attrs={'class': 'form-control'}),
            'date':         forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'location':     forms.TextInput(attrs={'class': 'form-control'}),
            'position':     forms.TextInput(attrs={'class': 'form-control'}),
            'work_type':    forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'title':        'Название наряда',
            'date':         'Дата',
            'location':     'Место выполнения',
            'position':     'Должность',
            'work_type':    'Вид работы',
            'instructions': 'Инструкции по ТБ',
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise forms.ValidationError('Название должно содержать минимум 5 символов')
        return title

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if not date:
            raise forms.ValidationError('Укажите дату')
        if not self.instance.pk and date < timezone.now().date():
            raise forms.ValidationError('Дата не может быть в прошлом')
        return date

    def clean_location(self):
        location = self.cleaned_data.get('location', '').strip()
        if len(location) < 3:
            raise forms.ValidationError('Минимум 3 символа')
        return location

    def clean_work_type(self):
        work_type = self.cleaned_data.get('work_type', '').strip()
        if len(work_type) < 10:
            raise forms.ValidationError('Опишите подробнее (минимум 10 символов)')
        return work_type

    def clean_instructions(self):
        instructions = self.cleaned_data.get('instructions', '').strip()
        if len(instructions) < 10:
            raise forms.ValidationError('Укажите инструкции (минимум 10 символов)')
        return instructions

    def clean(self):
        cleaned_data = super().clean()
        senior = cleaned_data.get('senior')
        workers = cleaned_data.get('workers')
        if senior and workers and senior in workers:
            raise forms.ValidationError(
                'Старший наряда не должен быть в списке работников'
            )
        return cleaned_data


class WorkOrderEditForm(forms.ModelForm):
    """Форма редактирования — без изменения состава бригады."""

    class Meta:
        model = WorkOrder
        fields = ['title', 'date', 'location', 'position', 'work_type', 'instructions']
        widgets = {
            'title':        forms.TextInput(attrs={'class': 'form-control'}),
            'date':         forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'location':     forms.TextInput(attrs={'class': 'form-control'}),
            'position':     forms.TextInput(attrs={'class': 'form-control'}),
            'work_type':    forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'title':        'Название наряда',
            'date':         'Дата',
            'location':     'Место выполнения',
            'position':     'Должность',
            'work_type':    'Вид работы',
            'instructions': 'Инструкции по ТБ',
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise forms.ValidationError('Название должно содержать минимум 5 символов')
        return title

    def clean_work_type(self):
        work_type = self.cleaned_data.get('work_type', '').strip()
        if len(work_type) < 10:
            raise forms.ValidationError('Опишите подробнее (минимум 10 символов)')
        return work_type

    def clean_instructions(self):
        instructions = self.cleaned_data.get('instructions', '').strip()
        if len(instructions) < 10:
            raise forms.ValidationError('Укажите инструкции (минимум 10 символов)')
        return instructions