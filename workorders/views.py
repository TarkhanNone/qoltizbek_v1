from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.views.generic import ListView, DetailView
from django.core.exceptions import ObjectDoesNotExist

from .models import WorkOrder, Brigade, BrigadeMember, Signature, AuditLog
from .forms import WorkOrderForm, WorkOrderEditForm


# ─── КОНСТАНТЫ РОЛЕЙ ───────────────────────────────────────────
ISSUER_GROUPS = ['Руководитель']
LEADER_GROUPS = ['Старший наряда']
WORKER_GROUPS = ['Работник']

ROLE_NAMES = {
    'issuer': 'Выдал наряд',
    'leader': 'Старший наряда',
    'worker': 'Работник',
}


# ─── УТИЛИТЫ ───────────────────────────────────────────────────
def log_action(user, workorder, action, description=''):
    AuditLog.objects.create(
        user=user,
        work_order=workorder,
        action=action,
        description=description
    )


def is_in_brigade(user, workorder):
    try:
        return workorder.brigade.members.filter(user=user).exists()
    except (ObjectDoesNotExist, AttributeError):
        return False


def can_sign(user, workorder):
    if workorder.status == 'closed':
        return False
    if not user.is_authenticated:
        return False

    roles = set(workorder.signatures.values_list('role', flat=True))
    groups = set(user.groups.values_list('name', flat=True))

    # Руководитель — подписывает первым
    if groups & set(ISSUER_GROUPS):
        return 'issuer' not in roles and workorder.issuer == user

    # Старший наряда — после руководителя
    if groups & set(LEADER_GROUPS):
        return (
            'issuer' in roles
            and 'leader' not in roles
            and is_in_brigade(user, workorder)
        )

    # Работник — после старшего, каждый один раз
    if groups & set(WORKER_GROUPS):
        already_signed = workorder.signatures.filter(
            user=user, role='worker'
        ).exists()
        return (
            'leader' in roles
            and not already_signed
            and is_in_brigade(user, workorder)
        )

    return False


def get_role_for_user(user, workorder):
    groups = set(user.groups.values_list('name', flat=True))

    # Если создатель наряда — выдаёт
    if groups & set(ISSUER_GROUPS) and workorder.issuer == user:
        return 'issuer'

    # Если старший в бригаде
    try:
        if workorder.brigade.members.filter(user=user, is_leader=True).exists():
            return 'leader'
    except (ObjectDoesNotExist, AttributeError):
        pass

    return 'worker'


def update_status(workorder):
    if workorder.status == 'closed':
        return

    roles = set(workorder.signatures.values_list('role', flat=True))

    if 'issuer' not in roles:
        workorder.status = 'draft'
    elif 'leader' not in roles:
        workorder.status = 'progress'
    else:
        try:
            workers_count = workorder.brigade.members.filter(
                is_leader=False
            ).count()
            worker_signs = workorder.signatures.filter(role='worker').count()
            if worker_signs >= workers_count:
                workorder.status = 'done'
            else:
                workorder.status = 'progress'
        except (ObjectDoesNotExist, AttributeError):
            workorder.status = 'progress'

    workorder.save()


# ─── СПИСОК ────────────────────────────────────────────────────
class WorkOrderListView(ListView):
    model = WorkOrder
    template_name = 'workorders/list.html'
    context_object_name = 'workorders'
    paginate_by = 10

    def get_queryset(self):
        qs = WorkOrder.objects.filter(is_deleted=False).select_related(
            'issuer', 'assigned_to', 'brigade'
        ).prefetch_related(
            'signatures', 'brigade__members'
        )

        status = self.request.GET.get('status')
        search = self.request.GET.get('q')
        sort = self.request.GET.get('sort', '-created_at')
        can_sign_filter = self.request.GET.get('can_sign')

        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(location__icontains=search) |
                Q(work_type__icontains=search)
            )
        # Фильтр "На подпись" — показывает только те где пользователь может подписать
        if can_sign_filter and self.request.user.is_authenticated:
            signed_ids = Signature.objects.filter(
                user=self.request.user
            ).values_list('work_order_id', flat=True)

            groups = set(self.request.user.groups.values_list('name', flat=True))

            if groups & set(ISSUER_GROUPS):
                qs = qs.filter(status='draft').exclude(
                    signatures__role='issuer'
                )
            elif groups & set(LEADER_GROUPS):
                qs = qs.filter(
                    signatures__role='issuer'
                ).exclude(signatures__role='leader').filter(
                    brigade__members__user=self.request.user
                )
            elif groups & set(WORKER_GROUPS):
                qs = qs.filter(
                    signatures__role='leader'
                ).filter(
                    brigade__members__user=self.request.user
                ).exclude(
                    id__in=signed_ids
                )
            return qs.distinct()

        allowed = ['title', '-title', 'date', '-date',
                   'status', '-status', 'created_at', '-created_at']
        qs = qs.order_by(sort if sort in allowed else '-created_at')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_filter'] = self.request.GET.get('status', '')
        ctx['search']        = self.request.GET.get('q', '')
        ctx['sort']          = self.request.GET.get('sort', '-created_at')
        return ctx


# ─── ПРОСМОТР ──────────────────────────────────────────────────
class WorkOrderDetailView(DetailView):
    model = WorkOrder
    template_name = 'workorders/detail.html'
    context_object_name = 'workorder'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['can_sign'] = can_sign(user, self.object) if user.is_authenticated else False
        ctx['roles'] = set(self.object.signatures.values_list('role', flat=True))
        ctx['can_close'] = (
            user.is_authenticated
            and self.object.status == 'done'
            and set(user.groups.values_list('name', flat=True)) & set(ISSUER_GROUPS)
        )
        return ctx


# ─── СОЗДАНИЕ ──────────────────────────────────────────────────
@login_required
def workorder_create(request):
    if request.method == 'POST':
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    wo = form.save(commit=False)
                    wo.issuer = request.user
                    wo.assigned_to = form.cleaned_data['senior']
                    if not wo.position and request.user.position:
                        wo.position = request.user.position
                    wo.save()

                    brigade = Brigade.objects.create(
                        name=f"Бригада — {wo.title}",
                        work_order=wo
                    )
                    BrigadeMember.objects.create(
                        brigade=brigade,
                        user=form.cleaned_data['senior'],
                        is_leader=True
                    )
                    for worker in form.cleaned_data['workers']:
                        BrigadeMember.objects.create(
                            brigade=brigade,
                            user=worker,
                            is_leader=False
                        )

                    log_action(request.user, wo, 'create', 'Создан наряд')

                messages.success(request, 'Наряд создан.')
                return redirect('workorder_detail', pk=wo.pk)

            except Exception as e:
                messages.error(request, f'Ошибка: {e}')
    else:
        initial = {}
        if hasattr(request.user, 'position') and request.user.position:
            initial['position'] = request.user.position
        form = WorkOrderForm(initial=initial)

    return render(request, 'workorders/form.html', {
        'form': form, 'title': 'Создать наряд'
    })


# ─── РЕДАКТИРОВАНИЕ ────────────────────────────────────────────
@login_required
def workorder_update(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, is_deleted=False)

    if not (request.user.is_staff or wo.issuer == request.user):
        messages.error(request, 'Нет прав на редактирование.')
        return redirect('workorder_detail', pk=pk)

    if request.method == 'POST':
        form = WorkOrderEditForm(request.POST, instance=wo)
        if form.is_valid():
            form.save()
            log_action(request.user, wo, 'update', 'Обновлён наряд')
            messages.success(request, 'Наряд обновлён.')
            return redirect('workorder_detail', pk=wo.pk)
    else:
        form = WorkOrderEditForm(instance=wo)

    return render(request, 'workorders/form.html', {
        'form': form, 'title': 'Редактировать наряд'
    })


# ─── УДАЛЕНИЕ ──────────────────────────────────────────────────
@login_required
def workorder_delete(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, is_deleted=False)

    if not (request.user.is_staff or wo.issuer == request.user):
        messages.error(request, 'Нет прав на удаление.')
        return redirect('workorder_detail', pk=pk)

    wo.is_deleted = True
    wo.save()
    log_action(request.user, wo, 'delete', 'Мягкое удаление')
    messages.success(request, 'Наряд удалён.')
    return redirect('workorder_list')


# ─── ПОДПИСАНИЕ ────────────────────────────────────────────────
@login_required
def sign_workorder(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, is_deleted=False)

    if not can_sign(request.user, wo):
        messages.error(request, 'Вы не можете подписать этот наряд сейчас.')
        return redirect('workorder_detail', pk=pk)

    role = get_role_for_user(request.user, wo)
    Signature.objects.get_or_create(work_order=wo, user=request.user, role=role)
    log_action(request.user, wo, 'sign', ROLE_NAMES.get(role, role))
    update_status(wo)

    messages.success(request, f'Подпись «{ROLE_NAMES.get(role, role)}» поставлена.')
    return redirect('workorder_detail', pk=pk)


# ─── ЗАКРЫТИЕ ──────────────────────────────────────────────────
@login_required
def close_workorder(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, is_deleted=False)

    groups = set(request.user.groups.values_list('name', flat=True))
    if not (groups & set(ISSUER_GROUPS)):
        messages.error(request, 'Только руководитель может закрыть наряд.')
        return redirect('workorder_detail', pk=pk)

    if wo.status != 'done':
        messages.error(request, 'Наряд не может быть закрыт — не все подписи собраны.')
        return redirect('workorder_detail', pk=pk)

    wo.status = 'closed'
    wo.save()
    log_action(request.user, wo, 'close', 'Наряд закрыт руководителем')
    messages.success(request, 'Наряд закрыт.')
    return redirect('workorder_detail', pk=pk)


# ─── DASHBOARD ─────────────────────────────────────────────────
@login_required
def dashboard(request):
    qs = WorkOrder.objects.filter(is_deleted=False)
    context = {
        'total':    qs.count(),
        'draft':    qs.filter(status='draft').count(),
        'progress': qs.filter(status='progress').count(),
        'done':     qs.filter(status='done').count(),
        'closed':   qs.filter(status='closed').count(),
        'recent':   qs.order_by('-created_at')[:5],
    }
    return render(request, 'workorders/dashboard.html', context)


# ─── ПЕЧАТЬ ────────────────────────────────────────────────────
@login_required
def print_workorder(request, pk):
    wo = get_object_or_404(WorkOrder, pk=pk, is_deleted=False)
    return render(request, 'workorders/print.html', {'workorder': wo})

# ─── Настройки ────────────────────────────────────────────────────
@login_required
def settings_view(request):
    return render(request, 'workorders/settings.html')