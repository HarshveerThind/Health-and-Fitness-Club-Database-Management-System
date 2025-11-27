from datetime import datetime
from sqlalchemy import and_, or_
from . import db
from .schema import (
    Member,
    Trainer,
    FitnessGoal,
    HealthMetric,
    Room,
    ClassSession,
    ClassRegistration,
    PTSession,
    TrainerAvailability,
    Invoice,
)


# ---------- Helper functions ----------

def parse_datetime_local(dt_str: str):
    """
    Handle HTML datetime-local input (YYYY-MM-DDTHH:MM).
    """
    if not dt_str:
        return None
    return datetime.fromisoformat(dt_str)


def ranges_overlap(start_a, end_a, start_b, end_b):
    return not (end_a <= start_b or end_b <= start_a)


def check_room_conflict(room_id, start, end, exclude_class_id=None, exclude_pt_id=None):
    class_conflicts = ClassSession.query.filter(
        ClassSession.room_id == room_id,
        ClassSession.id != (exclude_class_id or 0),
        and_(ClassSession.start_time < end, ClassSession.end_time > start),
    ).count()

    pt_conflicts = PTSession.query.filter(
        PTSession.room_id == room_id,
        PTSession.id != (exclude_pt_id or 0),
        and_(PTSession.start_time < end, PTSession.end_time > start),
    ).count()

    return (class_conflicts + pt_conflicts) > 0


def check_trainer_conflict(trainer_id, start, end, exclude_class_id=None, exclude_pt_id=None):
    class_conflicts = ClassSession.query.filter(
        ClassSession.trainer_id == trainer_id,
        ClassSession.id != (exclude_class_id or 0),
        and_(ClassSession.start_time < end, ClassSession.end_time > start),
    ).count()

    pt_conflicts = PTSession.query.filter(
        PTSession.trainer_id == trainer_id,
        PTSession.id != (exclude_pt_id or 0),
        and_(PTSession.start_time < end, PTSession.end_time > start),
    ).count()

    return (class_conflicts + pt_conflicts) > 0


# ---------- Member operations ----------

def register_member(name, email, dob_str=None, gender=None, phone=None):
    existing = Member.query.filter_by(email=email).first()
    if existing:
        raise ValueError("Email already registered.")

    dob = datetime.strptime(dob_str, "%Y-%m-%d") if dob_str else None
    member = Member(
        name=name,
        email=email,
        date_of_birth=dob,
        gender=gender,
        phone=phone,
    )
    db.session.add(member)
    db.session.commit()
    return member


def update_member_profile(member_id, name, gender=None, phone=None,
                          goal_description=None, target_weight=None):
    member = Member.query.get(member_id)
    if not member:
        raise ValueError("Member not found.")

    member.name = name
    member.gender = gender
    member.phone = phone

    if goal_description or target_weight:
        member.goals.update({"is_active": False})
        new_goal = FitnessGoal(
            member_id=member.id,
            description=goal_description or "",
            target_weight_kg=float(target_weight) if target_weight else None,
            is_active=True,
        )
        db.session.add(new_goal)

    db.session.commit()
    return member


def add_health_metric(member_id, height_cm=None, weight_kg=None, heart_rate_bpm=None):
    member = Member.query.get(member_id)
    if not member:
        raise ValueError("Member not found.")

    metric = HealthMetric(
        member_id=member.id,
        height_cm=float(height_cm) if height_cm else None,
        weight_kg=float(weight_kg) if weight_kg else None,
        heart_rate_bpm=float(heart_rate_bpm) if heart_rate_bpm else None,
        recorded_at=datetime.utcnow(),
    )
    db.session.add(metric)
    db.session.commit()
    return metric


def get_member_dashboard_data(member_id):
    member = Member.query.get(member_id)
    if not member:
        raise ValueError("Member not found.")

    latest_metric = (
        HealthMetric.query.filter_by(member_id=member.id)
        .order_by(HealthMetric.recorded_at.desc())
        .first()
    )

    active_goal = (
        FitnessGoal.query.filter_by(member_id=member.id, is_active=True)
        .order_by(FitnessGoal.created_at.desc())
        .first()
    )

    now = datetime.utcnow()
    past_classes_count = (
        ClassRegistration.query.join(ClassSession)
        .filter(
            ClassRegistration.member_id == member.id,
            ClassSession.end_time < now,
        )
        .count()
    )

    upcoming_pt_sessions = (
        PTSession.query.filter(
            PTSession.member_id == member.id,
            PTSession.start_time >= now,
        )
        .order_by(PTSession.start_time)
        .all()
    )

    return {
        "member": member,
        "latest_metric": latest_metric,
        "active_goal": active_goal,
        "past_classes_count": past_classes_count,
        "upcoming_pt_sessions": upcoming_pt_sessions,
    }


def get_all_members():
    return Member.query.order_by(Member.id).all()


# ---------- Trainer operations ----------

def set_trainer_availability(trainer_id, start_str, end_str):
    trainer = Trainer.query.get(trainer_id)
    if not trainer:
        raise ValueError("Trainer not found.")

    start = parse_datetime_local(start_str)
    end = parse_datetime_local(end_str)
    if not start or not end or start >= end:
        raise ValueError("Invalid time range.")

    existing_slots = TrainerAvailability.query.filter_by(trainer_id=trainer.id).all()
    for slot in existing_slots:
        if ranges_overlap(start, end, slot.start_time, slot.end_time):
            raise ValueError("Time slot overlaps existing availability.")

    new_slot = TrainerAvailability(trainer_id=trainer.id, start_time=start, end_time=end)
    db.session.add(new_slot)
    db.session.commit()
    return new_slot


def get_trainer_schedule(trainer_id):
    trainer = Trainer.query.get(trainer_id)
    if not trainer:
        raise ValueError("Trainer not found.")

    classes = (
        ClassSession.query.filter_by(trainer_id=trainer.id)
        .order_by(ClassSession.start_time)
        .all()
    )
    pt_sessions = (
        PTSession.query.filter_by(trainer_id=trainer.id)
        .order_by(PTSession.start_time)
        .all()
    )
    availabilities = (
        TrainerAvailability.query.filter_by(trainer_id=trainer.id)
        .order_by(TrainerAvailability.start_time)
        .all()
    )

    return {
        "trainer": trainer,
        "classes": classes,
        "pt_sessions": pt_sessions,
        "availabilities": availabilities,
    }


def search_members_by_name(term):
    if not term:
        return []
    return Member.query.filter(Member.name.ilike(f"%{term}%")).order_by(Member.name).all()


def get_all_trainers():
    return Trainer.query.order_by(Trainer.id).all()


# ---------- Admin operations ----------

def create_class_session(title, trainer_id, room_id, start_str, end_str, capacity):
    trainer = Trainer.query.get(trainer_id)
    room = Room.query.get(room_id)
    if not trainer:
        raise ValueError("Trainer not found.")
    if not room:
        raise ValueError("Room not found.")

    start = parse_datetime_local(start_str)
    end = parse_datetime_local(end_str)
    if not start or not end or start >= end:
        raise ValueError("Invalid time range.")

    if check_room_conflict(room_id, start, end):
        raise ValueError("Room is already booked at that time.")
    if check_trainer_conflict(trainer_id, start, end):
        raise ValueError("Trainer is already booked at that time.")

    class_session = ClassSession(
        title=title,
        trainer_id=trainer_id,
        room_id=room_id,
        start_time=start,
        end_time=end,
        capacity=int(capacity),
    )
    db.session.add(class_session)
    db.session.commit()
    return class_session


def create_pt_session(member_id, trainer_id, room_id, start_str, end_str):
    member = Member.query.get(member_id)
    trainer = Trainer.query.get(trainer_id)
    room = Room.query.get(room_id)

    if not member:
        raise ValueError("Member not found.")
    if not trainer:
        raise ValueError("Trainer not found.")
    if not room:
        raise ValueError("Room not found.")

    start = parse_datetime_local(start_str)
    end = parse_datetime_local(end_str)
    if not start or not end or start >= end:
        raise ValueError("Invalid time range.")

    if check_room_conflict(room_id, start, end):
        raise ValueError("Room is already booked at that time.")
    if check_trainer_conflict(trainer_id, start, end):
        raise ValueError("Trainer is already booked at that time.")

    pt = PTSession(
        member_id=member_id,
        trainer_id=trainer_id,
        room_id=room_id,
        start_time=start,
        end_time=end,
        status="Scheduled",
    )
    db.session.add(pt)
    db.session.commit()
    return pt


def create_invoice(member_id, description, amount, payment_method=None):
    member = Member.query.get(member_id)
    if not member:
        raise ValueError("Member not found.")

    invoice = Invoice(
        member_id=member_id,
        description=description or "",
        amount=amount,
        status="Unpaid",
        payment_method=payment_method,
    )
    db.session.add(invoice)
    db.session.commit()
    return invoice


def mark_invoice_paid(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        raise ValueError("Invoice not found.")

    invoice.status = "Paid"
    invoice.paid_at = datetime.utcnow()
    db.session.commit()
    return invoice


def get_admin_portal_data():
    trainers = get_all_trainers()
    rooms = Room.query.order_by(Room.id).all()
    members = get_all_members()
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()

    return {
        "trainers": trainers,
        "rooms": rooms,
        "members": members,
        "invoices": invoices,
    }
