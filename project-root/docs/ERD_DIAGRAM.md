```mermaid
erDiagram

  MEMBER {
    int id PK
    string name
    string email
    date date_of_birth
    string gender
    string phone
    datetime created_at
  }

  TRAINER {
    int id PK
    string name
    string email
  }

  ADMIN_USER {
    int id PK
    string name
    string email
  }

  FITNESS_GOAL {
    int id PK
    int member_id FK
    string description
    float target_weight_kg
    float target_body_fat
    bool is_active
    datetime created_at
  }

  HEALTH_METRIC {
    int id PK
    int member_id FK
    float height_cm
    float weight_kg
    float heart_rate_bpm
    datetime recorded_at
  }

  ROOM {
    int id PK
    string name
    int capacity
    string location
  }

  CLASS_SESSION {
    int id PK
    string title
    int trainer_id FK
    int room_id FK
    datetime start_time
    datetime end_time
    int capacity
  }

  CLASS_REGISTRATION {
    int id PK
    int member_id FK
    int class_session_id FK
    datetime registered_at
  }

  PT_SESSION {
    int id PK
    int member_id FK
    int trainer_id FK
    int room_id FK
    datetime start_time
    datetime end_time
    string status
  }

  TRAINER_AVAILABILITY {
    int id PK
    int trainer_id FK
    datetime start_time
    datetime end_time
  }

  INVOICE {
    int id PK
    int member_id FK
    string description
    numeric amount
    string status
    datetime created_at
    datetime paid_at
    string payment_method
  }

  MEMBER ||--o{ FITNESS_GOAL : has
  MEMBER ||--o{ HEALTH_METRIC : has
  MEMBER ||--o{ CLASS_REGISTRATION : registers
  MEMBER ||--o{ PT_SESSION : books
  MEMBER ||--o{ INVOICE : billed

  TRAINER ||--o{ CLASS_SESSION : teaches
  TRAINER ||--o{ PT_SESSION : trains
  TRAINER ||--o{ TRAINER_AVAILABILITY : available

  ROOM ||--o{ CLASS_SESSION : hosts
  ROOM ||--o{ PT_SESSION : hosts

  CLASS_SESSION ||--o{ CLASS_REGISTRATION : includes