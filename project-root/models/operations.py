from datetime import datetime

from . import db
from .schema import (
    Member,
    Trainer,
    AdminUser,
    FitnessGoal,
    HealthMetric,
    Room,
    ClassSession,
    ClassRegistration,
    PTSession,
    TrainerAvailability,
    Invoice,
)


# ---------- helpers ----------

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_datetime_local(dt_str):
    if not dt_str:
        return None
    try:
        # HTML datetime-local gives "YYYY-MM-DDTHH:MM"
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def check_room_conflict(room_id, start, end, exclude_class_id=None, exclude_pt_id=None):
    """
    Return True if there is any class or PT session in this room overlapping [start, end).
    """
    if not room_id or not start or not end:
        return False

    # overlapping if not (existing.end <= start or existing.start >= end)
    class_q = ClassSession.query.filter(ClassSession.room_id == room_id)
    if exclude_class_id is not None:
        class_q = class_q.filter(ClassSession.id != exclude_class_id)
    class_q = class_q.filter(
        ClassSession.start_time < end,
        ClassSession.end_time > start,
    )

    pt_q = PTSession.query.filter(PTSession.room_id == room_id)
    if exclude_pt_id is not None:
        pt_q = pt_q.filter(PTSession.id != exclude_pt_id)
    pt_q = pt_q.filter(
        PTSession.start_time < end,
        PTSession.end_time > start,
    )

    return class_q.first() is not None or pt_q.first() is not None


def check_trainer_conflict(trainer_id, start, end, exclude_class_id=None, exclude_pt_id=None):
    if not trainer_id or not start or not end:
        return False

    class_q = ClassSession.query.filter(ClassSession.trainer_id == trainer_id)
    if exclude_class_id is not None:
        class_q = class_q.filter(ClassSession.id != exclude_class_id)
    class_q = class_q.filter(
        ClassSession.start_time < end,
        ClassSession.end_time > start,
    )

    pt_q = PTSession.query.filter(PTSession.trainer_id == trainer_id)
    if exclude_pt_id is not None:
        pt_q = pt_q.filter(PTSession.id != exclude_pt_id)
    pt_q = pt_q.filter(
        PTSession.start_time < end,
        PTSession.end_time > start,
    )

    return class_q.first() is not None or pt_q.first() is not None


# ---------- seeding ----------

def ensure_default_rooms():
    """
    Create 10 default rooms if none exist.
    """
    if Room.query.count() == 0:
        rooms = []
        for i in range(1, 11):
            rooms.append(
                Room(
                    name=f"Room {i}",
                    capacity=20,
                    location=f"Floor 1 - {i}",
                )
            )
        db.session.add_all(rooms)
        db.session.commit()


# ---------- member operations ----------

def register_member(name, email, dob_str, gender, phone):
    if not name or not email:
        raise ValueError("Name and email are required.")

    existing = Member.query.filter_by(email=email).first()
    if existing:
        raise ValueError("Email already registered.")

    dob = parse_date(dob_str)

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


def update_member_profile(member_id, name, gender, phone, goal_description, target_weight_kg):
    member = Member.query.get(member_id)
    if not member:
        raise ValueError("Member not found.")

    if name:
        member.name = name
    if gender:
        member.gender = gender
    if phone:
        member.phone = phone

    if goal_description:
        # mark existing goals inactive
        FitnessGoal.query.filter_by(member_id=member_id, is_active=True).update(
            {"is_active": False}
        )
        goal = FitnessGoal(
            member_id=member_id,
            description=goal_description,
            target_weight_kg=float(target_weight_kg) if target_weight_kg else None,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db.session.add(goal)

    db.session.commit()
    return member


def add_health_metric(member_id, height_cm, weight_kg, heart_rate_bpm):
    member = Member.query.get(member_id)
    if not member:
        raise ValueError("Member not found.")

    metric = HealthMetric(
        member_id=member_id,
        height_cm=float(height_cm) if height_cm else None,
        weight_kg=float(weight_kg) if weight_kg else None,
        heart_rate_bpm=int(heart_rate_bpm) if heart_rate_bpm else None,
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
        HealthMetric.query.filter_by(member_id=member_id)
        .order_by(HealthMetric.recorded_at.desc())
        .first()
    )
    active_goal = (
        FitnessGoal.query.filter_by(member_id=member_id, is_active=True)
        .order_by(FitnessGoal.created_at.desc())
        .first()
    )

    now = datetime.utcnow()

    past_classes_count = (
        db.session.query(ClassRegistration)
        .join(ClassSession, ClassRegistration.class_session_id == ClassSession.id)
        .filter(
            ClassRegistration.member_id == member_id,
            ClassSession.start_time < now,
        )
        .count()
    )

    upcoming_pt_sessions = (
        PTSession.query.filter_by(member_id=member_id)
        .filter(PTSession.start_time >= now)
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
    return Member.query.order_by(Member.name).all()


def get_upcoming_classes():
    now = datetime.utcnow()
    return (
        ClassSession.query
        .filter(ClassSession.start_time >= now)
        .order_by(ClassSession.start_time)
        .all()
    )


def register_member_for_class(member_id, class_session_id):
    member = Member.query.get(member_id)
    class_session = ClassSession.query.get(class_session_id)

    if not member:
        raise ValueError("Member not found.")
    if not class_session:
        raise ValueError("Class session not found.")

    existing = ClassRegistration.query.filter_by(
        member_id=member_id,
        class_session_id=class_session_id,
    ).first()
    if existing:
        raise ValueError("Already registered for this class.")

    current_count = ClassRegistration.query.filter_by(
        class_session_id=class_session_id
    ).count()
    if current_count >= class_session.capacity:
        raise ValueError("Class is already full.")

    reg = ClassRegistration(
        member_id=member_id,
        class_session_id=class_session_id,
    )
    db.session.add(reg)
    db.session.commit()
    return reg


# ---------- trainer operations ----------

def set_trainer_availability(trainer_id, start_str, end_str):
    trainer = Trainer.query.get(trainer_id)
    if not trainer:
        raise ValueError("Trainer not found.")

    start = parse_datetime_local(start_str)
    end = parse_datetime_local(end_str)
    if not start or not end or start >= end:
        raise ValueError("Invalid time range.")

    existing = TrainerAvailability.query.filter_by(trainer_id=trainer_id).filter(
        TrainerAvailability.start_time < end,
        TrainerAvailability.end_time > start,
    ).first()

    if existing:
        raise ValueError("Availability overlaps with an existing slot.")

    slot = TrainerAvailability(
        trainer_id=trainer_id,
        start_time=start,
        end_time=end,
    )
    db.session.add(slot)
    db.session.commit()
    return slot


def get_trainer_schedule(trainer_id):
    trainer = Trainer.query.get(trainer_id)
    if not trainer:
        raise ValueError("Trainer not found.")

    now = datetime.utcnow()

    classes = (
        ClassSession.query.filter_by(trainer_id=trainer_id)
        .filter(ClassSession.start_time >= now)
        .order_by(ClassSession.start_time)
        .all()
    )

    pt_sessions = (
        PTSession.query.filter_by(trainer_id=trainer_id)
        .filter(PTSession.start_time >= now)
        .order_by(PTSession.start_time)
        .all()
    )

    availability = (
        TrainerAvailability.query.filter_by(trainer_id=trainer_id)
        .order_by(TrainerAvailability.start_time)
        .all()
    )

    return {
        "trainer": trainer,
        "classes": classes,
        "pt_sessions": pt_sessions,
        "availability": availability,
    }


def search_members_by_name(term):
    if not term:
        return []

    members = Member.query.filter(
        Member.name.ilike(f"%{term}%")
    ).order_by(Member.name).all()

    results = []
    for m in members:
        last_metric = (
            HealthMetric.query.filter_by(member_id=m.id)
            .order_by(HealthMetric.recorded_at.desc())
            .first()
        )
        active_goal = (
            FitnessGoal.query.filter_by(member_id=m.id, is_active=True)
            .order_by(FitnessGoal.created_at.desc())
            .first()
        )
        results.append(
            {
                "member": m,
                "last_metric": last_metric,
                "active_goal": active_goal,
            }
        )
    return results


def get_all_trainers():
    return Trainer.query.order_by(Trainer.name).all()


# ---------- admin operations ----------

def create_trainer(name, email):
    if not name or not email:
        raise ValueError("Name and email are required.")

    existing = Trainer.query.filter_by(email=email).first()
    if existing:
        raise ValueError("Trainer email already exists.")

    trainer = Trainer(name=name, email=email)
    db.session.add(trainer)
    db.session.commit()
    return trainer


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
        capacity=int(capacity) if capacity else 10,
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

    # must be inside at least one availability slot
    availabilities = TrainerAvailability.query.filter_by(trainer_id=trainer.id).all()
    fits_availability = any(
        slot.start_time <= start and slot.end_time >= end for slot in availabilities
    )
    if not fits_availability:
        raise ValueError("Trainer is not available during this time.")

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


def create_invoice(member_id, description, amount, payment_method):
    member = Member.query.get(member_id)
    if not member:
        raise ValueError("Member not found.")

    invoice = Invoice(
        member_id=member_id,
        description=description,
        amount=float(amount),
        payment_method=payment_method,
        status="Unpaid",
        created_at=datetime.utcnow(),
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


def update_class_session_room(class_session_id, new_room_id):
    class_session = ClassSession.query.get(class_session_id)
    if not class_session:
        raise ValueError("Class session not found.")

    room = Room.query.get(new_room_id)
    if not room:
        raise ValueError("Room not found.")

    start = class_session.start_time
    end = class_session.end_time

    if check_room_conflict(new_room_id, start, end, exclude_class_id=class_session.id):
        raise ValueError("Room is already booked at that time.")

    class_session.room_id = new_room_id
    db.session.commit()
    return class_session


def update_pt_session_room(pt_session_id, new_room_id):
    pt_session = PTSession.query.get(pt_session_id)
    if not pt_session:
        raise ValueError("PT session not found.")

    room = Room.query.get(new_room_id)
    if not room:
        raise ValueError("Room not found.")

    start = pt_session.start_time
    end = pt_session.end_time

    if check_room_conflict(new_room_id, start, end, exclude_pt_id=pt_session.id):
        raise ValueError("Room is already booked at that time.")

    pt_session.room_id = new_room_id
    db.session.commit()
    return pt_session


def get_admin_portal_data():
    trainers = get_all_trainers()
    rooms = Room.query.order_by(Room.id).all()
    members = get_all_members()
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    class_sessions = ClassSession.query.order_by(ClassSession.start_time).all()
    pt_sessions = PTSession.query.order_by(PTSession.start_time).all()

    return {
        "trainers": trainers,
        "rooms": rooms,
        "members": members,
        "invoices": invoices,
        "class_sessions": class_sessions,
        "pt_sessions": pt_sessions,
    }
