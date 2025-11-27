from datetime import datetime
from . import db


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    goals = db.relationship("FitnessGoal", back_populates="member", lazy="dynamic")
    metrics = db.relationship("HealthMetric", back_populates="member", lazy="dynamic")
    class_registrations = db.relationship("ClassRegistration", back_populates="member")
    pt_sessions = db.relationship("PTSession", back_populates="member")
    invoices = db.relationship("Invoice", back_populates="member")

    def __repr__(self):
        return f"<Member {self.email}>"
    

class Trainer(db.Model):
    __tablename__ = "trainers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    availabilities = db.relationship("TrainerAvailability", back_populates="trainer")
    pt_sessions = db.relationship("PTSession", back_populates="trainer")
    class_sessions = db.relationship("ClassSession", back_populates="trainer")

    def __repr__(self):
        return f"<Trainer {self.email}>"


class AdminUser(db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f"<AdminUser {self.email}>"


class FitnessGoal(db.Model):
    __tablename__ = "fitness_goals"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    target_weight_kg = db.Column(db.Float, nullable=True)
    target_body_fat = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship("Member", back_populates="goals")


class HealthMetric(db.Model):
    __tablename__ = "health_metrics"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    height_cm = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    heart_rate_bpm = db.Column(db.Float, nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship("Member", back_populates="metrics")


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(255), nullable=True)

    class_sessions = db.relationship("ClassSession", back_populates="room")
    pt_sessions = db.relationship("PTSession", back_populates="room")


class ClassSession(db.Model):
    __tablename__ = "class_sessions"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey("trainers.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

    trainer = db.relationship("Trainer", back_populates="class_sessions")
    room = db.relationship("Room", back_populates="class_sessions")
    registrations = db.relationship("ClassRegistration", back_populates="class_session")


class ClassRegistration(db.Model):
    __tablename__ = "class_registrations"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    class_session_id = db.Column(
        db.Integer, db.ForeignKey("class_sessions.id"), nullable=False
    )
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship("Member", back_populates="class_registrations")
    class_session = db.relationship("ClassSession", back_populates="registrations")


class PTSession(db.Model):
    __tablename__ = "pt_sessions"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey("trainers.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="Scheduled")

    member = db.relationship("Member", back_populates="pt_sessions")
    trainer = db.relationship("Trainer", back_populates="pt_sessions")
    room = db.relationship("Room", back_populates="pt_sessions")


class TrainerAvailability(db.Model):
    __tablename__ = "trainer_availabilities"

    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey("trainers.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    trainer = db.relationship("Trainer", back_populates="availabilities")


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default="Unpaid")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)

    member = db.relationship("Member", back_populates="invoices")
