from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from models.operations import (
    register_member,
    update_member_profile,
    add_health_metric,
    get_member_dashboard_data,
    get_all_members,
    set_trainer_availability,
    get_trainer_schedule,
    search_members_by_name,
    get_all_trainers,
    create_class_session,
    create_pt_session,
    create_invoice,
    mark_invoice_paid,
    get_admin_portal_data,
    create_trainer,
    get_upcoming_classes,
    register_member_for_class,
    update_class_session_room,
    update_pt_session_room,
)

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    return render_template("home.html")


# ---------- Member portal ----------

@bp.route("/member", methods=["GET"])
def member_portal():
    members = get_all_members()
    member_id = request.args.get("member_id", type=int)
    dashboard_data = None
    upcoming_classes = get_upcoming_classes()

    if member_id:
        try:
            dashboard_data = get_member_dashboard_data(member_id)
        except ValueError as e:
            flash(str(e))

    return render_template(
        "member_portal.html",
        members=members,
        selected_member_id=member_id,
        dashboard_data=dashboard_data,
        upcoming_classes=upcoming_classes,
    )


@bp.route("/member/register", methods=["POST"])
def member_register_route():
    name = request.form.get("name")
    email = request.form.get("email")
    dob = request.form.get("dob")
    gender = request.form.get("gender")
    phone = request.form.get("phone")

    try:
        member = register_member(name, email, dob, gender, phone)
        flash("Member registered.")
        return redirect(url_for("main.member_portal", member_id=member.id))
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("main.member_portal"))


@bp.route("/member/profile", methods=["POST"])
def member_profile_route():
    member_id = request.form.get("member_id", type=int)
    name = request.form.get("name")
    gender = request.form.get("gender")
    phone = request.form.get("phone")
    goal_description = request.form.get("goal_description")
    target_weight = request.form.get("target_weight")

    try:
        update_member_profile(
            member_id,
            name,
            gender,
            phone,
            goal_description,
            target_weight,
        )
        flash("Profile updated.")
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("main.member_portal", member_id=member_id))


@bp.route("/member/metric", methods=["POST"])
def member_metric_route():
    member_id = request.form.get("member_id", type=int)
    height = request.form.get("height_cm")
    weight = request.form.get("weight_kg")
    hr = request.form.get("heart_rate_bpm")

    try:
        add_health_metric(member_id, height, weight, hr)
        flash("Health metric added.")
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("main.member_portal", member_id=member_id))


@bp.route("/member/class-register", methods=["POST"])
def member_class_register_route():
    member_id = request.form.get("member_id", type=int)
    class_id = request.form.get("class_session_id", type=int)

    try:
        register_member_for_class(member_id, class_id)
        flash("Registered for class.")
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("main.member_portal", member_id=member_id))


# ---------- Trainer portal ----------

@bp.route("/trainer", methods=["GET"])
def trainer_portal():
    trainers = get_all_trainers()
    trainer_id = request.args.get("trainer_id", type=int)
    search_term = request.args.get("search", "")
    schedule_data = None
    member_results = []

    if trainer_id:
        try:
            schedule_data = get_trainer_schedule(trainer_id)
        except ValueError as e:
            flash(str(e))

    if search_term:
        member_results = search_members_by_name(search_term)

    return render_template(
        "trainer_portal.html",
        trainers=trainers,
        selected_trainer_id=trainer_id,
        schedule_data=schedule_data,
        search_term=search_term,
        member_results=member_results,
    )


@bp.route("/trainer/availability", methods=["POST"])
def trainer_availability_route():
    trainer_id = request.form.get("trainer_id", type=int)
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    try:
        set_trainer_availability(trainer_id, start_time, end_time)
        flash("Availability added.")
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("main.trainer_portal", trainer_id=trainer_id))


# ---------- Admin portal ----------

@bp.route("/admin", methods=["GET"])
def admin_portal():
    data = get_admin_portal_data()
    return render_template(
        "admin_portal.html",
        trainers=data["trainers"],
        rooms=data["rooms"],
        members=data["members"],
        invoices=data["invoices"],
        class_sessions=data["class_sessions"],
        pt_sessions=data["pt_sessions"],
    )


@bp.route("/admin/trainer", methods=["POST"])
def admin_trainer_route():
    name = request.form.get("name")
    email = request.form.get("email")

    try:
        create_trainer(name, email)
        flash("Trainer created.")
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("main.admin_portal"))


@bp.route("/admin/class", methods=["POST"])
def admin_class_route():
    title = request.form.get("title")
    trainer_id = request.form.get("trainer_id", type=int)
    room_id = request.form.get("room_id", type=int)
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    capacity = request.form.get("capacity")

    try:
        create_class_session(title, trainer_id, room_id, start_time, end_time, capacity)
        flash("Class session created.")
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("main.admin_portal"))


@bp.route("/admin/ptsession", methods=["POST"])
def admin_ptsession_route():
    member_id = request.form.get("member_id", type=int)
    trainer_id = request.form.get("trainer_id", type=int)
    room_id = request.form.get("room_id", type=int)
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    try:
        create_pt_session(member_id, trainer_id, room_id, start_time, end_time)
        flash("PT session created.")
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("main.admin_portal"))


@bp.route("/admin/invoice", methods=["POST"])
def admin_invoice_route():
    member_id = request.form.get("member_id", type=int)
    description = request.form.get("description")
    amount = request.form.get("amount")
    payment_method = request.form.get("payment_method")

    try:
        create_invoice(member_id, description, amount, payment_method)
        flash("Invoice created.")
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("main.admin_portal"))


@bp.route("/admin/invoice/<int:invoice_id>/pay", methods=["POST"])
def admin_invoice_pay_route(invoice_id):
    try:
        mark_invoice_paid(invoice_id)
        flash("Invoice marked as paid.")
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("main.admin_portal"))


@bp.route("/admin/class/<int:class_id>/room", methods=["POST"])
def admin_class_update_room_route(class_id):
    new_room_id = request.form.get("room_id", type=int)
    try:
        update_class_session_room(class_id, new_room_id)
        flash("Class room updated.")
    except ValueError as e:
        flash(str(e))
    return redirect(url_for("main.admin_portal"))


@bp.route("/admin/ptsession/<int:pt_id>/room", methods=["POST"])
def admin_ptsession_update_room_route(pt_id):
    new_room_id = request.form.get("room_id", type=int)
    try:
        update_pt_session_room(pt_id, new_room_id)
        flash("PT session room updated.")
    except ValueError as e:
        flash(str(e))
    return redirect(url_for("main.admin_portal"))
