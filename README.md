Health and Fitness Club Management System
Author - Harshveer Thind

This project is a Flask based system backed by a relational database that manages the core operations of a health and fitness club. 
It supports members, trainers, rooms, group classes, personal training sessions and invoices. The goal is to practise real backend 
design and structured database management.

Features:

Member portal
- Select an existing member and load a dashboard
- Register new members with name, email, date of birth, gender and phone
- Update profile fields
- Set or replace an active fitness goal with an optional target weight
- Record health metrics including height, weight and heart rate
- View the latest recorded metric and the current active goal
- View past class attendance count
- View upcoming personal training sessions
- View upcoming group classes and register for a class with capacity checks

Trainer portal
- Select a trainer and view their schedule
- Add availability slots with overlap validation
- View upcoming group classes taught by the trainer
- View upcoming personal training sessions
- View availability windows
- Search members by name and see their active goal and latest metric

Admin portal
- Create new trainers and view current trainers
- View available rooms
- Create group class sessions with trainer, room, time window and capacity
- Create personal training sessions linking member, trainer, room and time window
- Validate time conflicts for trainers and rooms
- Create invoices for members with description, amount and payment method
- Mark invoices as paid which sets a paid timestamp
- Change assigned rooms for group classes and PT sessions

Tech stack:
- Python 3
- Flask
- Flask SQLAlchemy
- PostgreSQL (recommended) or SQLite
- HTML templates with Jinja and a basic CSS stylesheet
- Database schema and SQL helpers

The database schema is defined in models/schema.py and includes:
- Member, Trainer, AdminUser
- FitnessGoal, HealthMetric
- Room, ClassSession, ClassRegistration
- PTSession, TrainerAvailability
- Invoice

docs/ERD_DIAGRAM.md contains a Mermaid ERD diagram showing table relationships.

Project Structure:
project-root/
│ run.py
│ config.py
│ instance/fitness_club.db
│
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── templates/
│   └── static/style.css
│
└── models/
    ├── __init__.py
    ├── schema.py
    ├── operations.py
    └── setup.sql


Setup Virtual Envrionment and dependencies (mac):

python -m venv .venv
source .venv/bin/activate
pip install flask flask_sqlalchemy psycopg2-binary

Run the server:
python run.py
