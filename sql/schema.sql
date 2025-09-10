CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE user_role_assignments (
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    role_id INT REFERENCES user_roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);
CREATE TABLE sports (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE user_sports (
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    sport_id INT REFERENCES sports(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, sport_id)
);
CREATE TABLE forecast_sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    sport_id INT REFERENCES sports(id),
    source_id INT REFERENCES forecast_sources(id),
    location TEXT,
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    forecast_date DATE NOT NULL,
    data JSONB NOT NULL
);
CREATE TABLE equipment_status (
    id SERIAL PRIMARY KEY,
    status_name TEXT NOT NULL
);
CREATE TABLE equipment (
    id SERIAL PRIMARY KEY,
    owner_id INT REFERENCES users(id),
    sport_id INT REFERENCES sports(id),
    title TEXT NOT NULL,
    description TEXT,
    size TEXT,
    condition_id INT REFERENCES equipment_status(id),
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE equipment_images (
    id SERIAL PRIMARY KEY,
    equipment_id INT REFERENCES equipment(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL
);
CREATE TABLE equipment_bookings (
    id SERIAL PRIMARY KEY,
    equipment_id INT REFERENCES equipment(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id),
    start_date DATE,
    end_date DATE,
    deposit_amount NUMERIC(10,2),
    status TEXT
);
CREATE TABLE equipment_reviews (
    id SERIAL PRIMARY KEY,
    equipment_id INT REFERENCES equipment(id),
    reviewer_id INT REFERENCES users(id),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE equipment_tips (
    id SERIAL PRIMARY KEY,
    booking_id INT REFERENCES equipment_bookings(id),
    amount NUMERIC(10,2)
);
CREATE TABLE skill_videos (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    sport_id INT REFERENCES sports(id),
    video_url TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE skill_ai_reviews (
    id SERIAL PRIMARY KEY,
    skill_video_id INT REFERENCES skill_videos(id),
    review_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE coach_applications (
    id SERIAL PRIMARY KEY,
    skill_video_id INT REFERENCES skill_videos(id),
    coach_id INT REFERENCES users(id),
    price NUMERIC(10,2),
    experience TEXT,
    status TEXT DEFAULT 'pending'
);
CREATE TABLE coach_reviews (
    id SERIAL PRIMARY KEY,
    coach_id INT REFERENCES users(id),
    reviewer_id INT REFERENCES users(id),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT
);
CREATE TABLE schools (
    id SERIAL PRIMARY KEY,
    owner_id INT REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT,
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6)
);
CREATE TABLE school_reviews (
    id SERIAL PRIMARY KEY,
    school_id INT REFERENCES schools(id),
    reviewer_id INT REFERENCES users(id),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT
);
CREATE TABLE school_professors (
    school_id INT REFERENCES schools(id),
    professor_id INT REFERENCES users(id),
    PRIMARY KEY (school_id, professor_id)
);
CREATE TABLE professor_availability (
    id SERIAL PRIMARY KEY,
    professor_id INT REFERENCES users(id),
    day_of_week INT CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME,
    end_time TIME,
    location TEXT
);
CREATE TABLE student_profiles (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES users(id),
    sport_id INT REFERENCES sports(id),
    notes TEXT
);
CREATE TABLE travel_plans (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    destination TEXT,
    start_date DATE,
    end_date DATE,
    sport_id INT REFERENCES sports(id)
);
CREATE TABLE travel_matches (
    id SERIAL PRIMARY KEY,
    plan_id INT REFERENCES travel_plans(id),
    matched_user_id INT REFERENCES users(id)
);
CREATE TABLE retreats (
    id SERIAL PRIMARY KEY,
    host_id INT REFERENCES users(id),
    title TEXT,
    description TEXT,
    location TEXT,
    start_date DATE,
    end_date DATE,
    sport_id INT REFERENCES sports(id)
);
CREATE TABLE retreat_applications (
    id SERIAL PRIMARY KEY,
    retreat_id INT REFERENCES retreats(id),
    applicant_id INT REFERENCES users(id),
    status TEXT DEFAULT 'pending'
);
CREATE TABLE retreat_reviews (
    id SERIAL PRIMARY KEY,
    retreat_id INT REFERENCES retreats(id),
    reviewer_id INT REFERENCES users(id),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT
);