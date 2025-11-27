-- Index on members email
CREATE INDEX IF NOT EXISTS idx_members_email ON members(email);

-- View for member dashboard summary
CREATE OR REPLACE VIEW member_dashboard_view AS
SELECT
    m.id AS member_id,
    m.name,
    (SELECT hm.weight_kg
     FROM health_metrics hm
     WHERE hm.member_id = m.id
     ORDER BY hm.recorded_at DESC
     LIMIT 1) AS latest_weight_kg,
    (SELECT hm.heart_rate_bpm
     FROM health_metrics hm
     WHERE hm.member_id = m.id
     ORDER BY hm.recorded_at DESC
     LIMIT 1) AS latest_heart_rate_bpm,
    (SELECT fg.description
     FROM fitness_goals fg
     WHERE fg.member_id = m.id AND fg.is_active = TRUE
     ORDER BY fg.created_at DESC
     LIMIT 1) AS active_goal_description,
    (SELECT COUNT(*)
     FROM class_registrations cr
     JOIN class_sessions cs ON cs.id = cr.class_session_id
     WHERE cr.member_id = m.id
       AND cs.end_time < NOW()) AS past_classes_count
FROM members m;


-- Trigger to enforce class capacity
CREATE OR REPLACE FUNCTION check_class_capacity()
RETURNS TRIGGER AS $$
DECLARE
    current_count INTEGER;
    max_capacity INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO current_count
    FROM class_registrations
    WHERE class_session_id = NEW.class_session_id;

    SELECT capacity
    INTO max_capacity
    FROM class_sessions
    WHERE id = NEW.class_session_id;

    IF current_count >= max_capacity THEN
        RAISE EXCEPTION 'Class is full for session %', NEW.class_session_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_class_capacity ON class_registrations;

CREATE TRIGGER trg_check_class_capacity
BEFORE INSERT ON class_registrations
FOR EACH ROW
EXECUTE FUNCTION check_class_capacity();


-- Trigger to set paid_at when status becomes Paid
CREATE OR REPLACE FUNCTION set_paid_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'Paid' AND (OLD.status IS DISTINCT FROM 'Paid') THEN
        NEW.paid_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_paid_at ON invoices;

CREATE TRIGGER trg_set_paid_at
BEFORE UPDATE ON invoices
FOR EACH ROW
EXECUTE FUNCTION set_paid_at();
