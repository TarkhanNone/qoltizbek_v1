import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from workorders.models import WorkOrder, Brigade, BrigadeMember, Signature
from workorders.views import can_sign, update_status
from datetime import date, timedelta

User = get_user_model()


@pytest.fixture
def groups(db):
    g1, _ = Group.objects.get_or_create(name='Руководитель')
    g2, _ = Group.objects.get_or_create(name='Старший наряда')
    g3, _ = Group.objects.get_or_create(name='Работник')
    return {'boss': g1, 'senior': g2, 'worker': g3}


@pytest.fixture
def boss(db, groups):
    user = User.objects.create_user(username='boss_test', password='test1234')
    user.groups.add(groups['boss'])
    return user


@pytest.fixture
def senior(db, groups):
    user = User.objects.create_user(username='senior_test', password='test1234')
    user.groups.add(groups['senior'])
    return user


@pytest.fixture
def worker(db, groups):
    user = User.objects.create_user(username='worker_test', password='test1234')
    user.groups.add(groups['worker'])
    return user


@pytest.fixture
def workorder(db, boss, senior):
    wo = WorkOrder.objects.create(
        title='Тестовый наряд',
        date=date.today() + timedelta(days=1),
        location='Цех №1',
        work_type='Тестовый вид работы',
        instructions='Тестовые инструкции',
        issuer=boss,
        assigned_to=senior,
    )
    brigade = Brigade.objects.create(name='Тест бригада', work_order=wo)
    BrigadeMember.objects.create(brigade=brigade, user=senior, is_leader=True)
    return wo


@pytest.fixture
def workorder_with_worker(db, workorder, worker):
    BrigadeMember.objects.create(
        brigade=workorder.brigade,
        user=worker,
        is_leader=False
    )
    return workorder


# ─── ТЕСТЫ ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_boss_can_sign_first(workorder, boss):
    """Руководитель может подписать первым."""
    assert can_sign(boss, workorder) is True


@pytest.mark.django_db
def test_senior_cannot_sign_before_boss(workorder, senior):
    """Старший не может подписать до руководителя."""
    assert can_sign(senior, workorder) is False


@pytest.mark.django_db
def test_senior_can_sign_after_boss(workorder, boss, senior):
    """Старший может подписать после руководителя."""
    Signature.objects.create(work_order=workorder, user=boss, role='issuer')
    assert can_sign(senior, workorder) is True


@pytest.mark.django_db
def test_worker_cannot_sign_before_senior(workorder_with_worker, worker):
    """Работник не может подписать до старшего."""
    assert can_sign(worker, workorder_with_worker) is False


@pytest.mark.django_db
def test_worker_can_sign_after_senior(workorder_with_worker, boss, senior, worker):
    """Работник может подписать после старшего."""
    Signature.objects.create(work_order=workorder_with_worker, user=boss, role='issuer')
    Signature.objects.create(work_order=workorder_with_worker, user=senior, role='leader')
    assert can_sign(worker, workorder_with_worker) is True


@pytest.mark.django_db
def test_worker_cannot_sign_twice(workorder_with_worker, boss, senior, worker):
    """Работник не может подписать дважды."""
    Signature.objects.create(work_order=workorder_with_worker, user=boss, role='issuer')
    Signature.objects.create(work_order=workorder_with_worker, user=senior, role='leader')
    Signature.objects.create(work_order=workorder_with_worker, user=worker, role='worker')
    assert can_sign(worker, workorder_with_worker) is False


@pytest.mark.django_db
def test_status_draft_initially(workorder):
    """Начальный статус — черновик."""
    assert workorder.status == 'draft'


@pytest.mark.django_db
def test_status_progress_after_issuer(workorder, boss):
    """После подписи руководителя — в процессе."""
    Signature.objects.create(work_order=workorder, user=boss, role='issuer')
    update_status(workorder)
    workorder.refresh_from_db()
    assert workorder.status == 'progress'


@pytest.mark.django_db
def test_status_done_after_all_signed(workorder_with_worker, boss, senior, worker):
    """После всех подписей — завершён."""
    Signature.objects.create(work_order=workorder_with_worker, user=boss, role='issuer')
    Signature.objects.create(work_order=workorder_with_worker, user=senior, role='leader')
    Signature.objects.create(work_order=workorder_with_worker, user=worker, role='worker')
    update_status(workorder_with_worker)
    workorder_with_worker.refresh_from_db()
    assert workorder_with_worker.status == 'done'


@pytest.mark.django_db
def test_cannot_sign_closed_workorder(workorder, boss):
    """Нельзя подписать закрытый наряд."""
    workorder.status = 'closed'
    workorder.save()
    assert can_sign(boss, workorder) is False