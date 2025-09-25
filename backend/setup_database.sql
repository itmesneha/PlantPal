-- PlantPal Database Setup Script for AWS RDS PostgreSQL
-- Run this script after connecting to your RDS instance

-- Note: Database 'plantpal' and user 'plantpal_admin' already exist in RDS
-- This script sets up the tables and initial data

-- Grant schema privileges (RDS admin already has these, but ensuring they exist)
GRANT ALL ON SCHEMA public TO plantpal_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO plantpal_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO plantpal_admin;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    cognito_user_id VARCHAR NOT NULL UNIQUE,
    email VARCHAR NOT NULL UNIQUE,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_cognito_id ON users(cognito_user_id);
CREATE INDEX idx_users_email ON users(email);

-- Plants table
CREATE TABLE plants (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    species VARCHAR NOT NULL,
    common_name VARCHAR,
    current_health_score FLOAT DEFAULT 100.0,
    streak_days INTEGER DEFAULT 0,
    last_check_in TIMESTAMP WITH TIME ZONE,
    image_url VARCHAR,
    care_notes TEXT,
    location VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_plants_user_id ON plants(user_id);

-- Scan sessions table
CREATE TABLE scan_sessions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plant_id VARCHAR REFERENCES plants(id) ON DELETE CASCADE,
    original_image_url VARCHAR NOT NULL,
    identified_species VARCHAR,
    confidence_score FLOAT,
    is_healthy BOOLEAN DEFAULT TRUE,
    disease_detected VARCHAR,
    health_score FLOAT,
    ai_model_version VARCHAR,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_scan_sessions_user_id ON scan_sessions(user_id);
CREATE INDEX idx_scan_sessions_plant_id ON scan_sessions(plant_id);

-- Health reports table
CREATE TABLE health_reports (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    scan_session_id VARCHAR NOT NULL REFERENCES scan_sessions(id) ON DELETE CASCADE,
    plant_id VARCHAR NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    overall_health_score FLOAT NOT NULL,
    leaf_condition VARCHAR,
    pest_issues JSONB,
    disease_indicators JSONB,
    watering_recommendation VARCHAR,
    light_recommendation VARCHAR,
    humidity_recommendation VARCHAR,
    fertilizer_recommendation VARCHAR,
    care_recommendations JSONB,
    estimated_light_level VARCHAR,
    estimated_humidity FLOAT,
    soil_moisture_level VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_health_reports_scan_session ON health_reports(scan_session_id);
CREATE INDEX idx_health_reports_plant_id ON health_reports(plant_id);

-- Achievements table
CREATE TABLE achievements (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR,
    achievement_type VARCHAR NOT NULL,
    requirement_value INTEGER NOT NULL,
    points_awarded INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User achievements table
CREATE TABLE user_achievements (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id VARCHAR NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    current_progress INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, achievement_id)
);

CREATE INDEX idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX idx_user_achievements_achievement_id ON user_achievements(achievement_id);

-- Plant care logs table
CREATE TABLE plant_care_logs (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    plant_id VARCHAR NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR NOT NULL,
    notes TEXT,
    image_url VARCHAR,
    scheduled_date TIMESTAMP WITH TIME ZONE,
    completed_date TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_plant_care_logs_plant_id ON plant_care_logs(plant_id);
CREATE INDEX idx_plant_care_logs_user_id ON plant_care_logs(user_id);

-- Plant species reference table
CREATE TABLE plant_species (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    scientific_name VARCHAR NOT NULL UNIQUE,
    common_names JSONB,
    family VARCHAR,
    care_difficulty VARCHAR,
    light_requirements VARCHAR,
    water_frequency VARCHAR,
    humidity_preference VARCHAR,
    temperature_range VARCHAR,
    description TEXT,
    characteristics JSONB,
    reference_images JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_plant_species_scientific_name ON plant_species(scientific_name);
CREATE INDEX idx_plant_species_common_names ON plant_species USING GIN(common_names);

-- Insert default achievements
INSERT INTO achievements (name, description, icon, achievement_type, requirement_value, points_awarded) VALUES
('First Scan', 'Complete your first plant scan', '🌱', 'scans_count', 1, 10),
('Green Thumb', 'Add your first plant to the garden', '👍', 'plants_count', 1, 15),
('Plant Parent', 'Collect 5 plants in your garden', '🌿', 'plants_count', 5, 50),
('Week Warrior', 'Maintain a 7-day streak', '🔥', 'streak', 7, 25),
('Plant Whisperer', 'Maintain a 30-day streak', '🏆', 'streak', 30, 100),
('Scanner Pro', 'Complete 50 plant scans', '📸', 'scans_count', 50, 75),
('Health Expert', 'Identify 10 plant health issues', '🩺', 'health_checks', 10, 60),
('Garden Master', 'Collect 20 plants in your garden', '🌺', 'plants_count', 20, 150);

-- Insert common plant species
INSERT INTO plant_species (scientific_name, common_names, family, care_difficulty, light_requirements, water_frequency, humidity_preference, temperature_range, description) VALUES
('Monstera deliciosa', '["Monstera", "Swiss Cheese Plant", "Split-leaf Philodendron"]', 'Araceae', 'Easy', 'Bright, indirect light', 'Weekly, when soil is dry', 'High (60-80%)', '18-27°C (65-80°F)', 'Popular houseplant with large, glossy leaves that develop characteristic splits and holes as they mature.'),
('Sansevieria trifasciata', '["Snake Plant", "Mother-in-Law''s Tongue", "Viper''s Bowstring Hemp"]', 'Asparagaceae', 'Easy', 'Low to bright, indirect light', 'Every 2-3 weeks, drought tolerant', 'Low to moderate', '15-27°C (60-80°F)', 'Extremely hardy plant with upright, sword-like leaves with yellow edges. Perfect for beginners.'),
('Epipremnum aureum', '["Golden Pothos", "Devil''s Ivy", "Money Plant"]', 'Araceae', 'Easy', 'Low to bright, indirect light', 'Weekly, when soil is dry', 'Moderate', '18-27°C (65-80°F)', 'Trailing vine with heart-shaped leaves, often variegated with yellow. Very forgiving and fast-growing.'),
('Ficus lyrata', '["Fiddle Leaf Fig", "Banjo Fig"]', 'Moraceae', 'Moderate', 'Bright, indirect light', 'Weekly, when top soil is dry', 'Moderate to high', '18-24°C (65-75°F)', 'Statement plant with large, violin-shaped leaves. Requires consistent care and stable conditions.'),
('Spathiphyllum wallisii', '["Peace Lily", "Spath"]', 'Araceae', 'Easy', 'Low to medium, indirect light', 'Weekly, keep soil moist', 'High', '18-27°C (65-80°F)', 'Elegant plant with dark green leaves and white flower spathes. Great air purifier.');

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_plants_updated_at BEFORE UPDATE ON plants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_achievements_updated_at BEFORE UPDATE ON user_achievements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_plant_species_updated_at BEFORE UPDATE ON plant_species FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Final permissions for RDS
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO plantpal_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO plantpal_admin;

-- Success message
SELECT 'PlantPal database setup complete! 🌱' AS message;