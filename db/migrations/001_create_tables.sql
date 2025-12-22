-- Створення таблиці travel_plans
CREATE TABLE IF NOT EXISTS travel_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL CHECK (length(title) > 0),
    description TEXT,
    start_date DATE,
    end_date DATE CHECK (end_date >= start_date),
    budget DECIMAL(10,2) CHECK (budget >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD' CHECK (length(currency) = 3),
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Створення таблиці locations
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    travel_plan_id UUID NOT NULL REFERENCES travel_plans(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    address TEXT,
    latitude DECIMAL(10,6) CHECK (latitude IS NULL OR (latitude >= -90 AND latitude <= 90)),
    longitude DECIMAL(11,6) CHECK (longitude IS NULL OR (longitude >= -180 AND longitude <= 180)),
    visit_order INTEGER NOT NULL CHECK (visit_order > 0),
    arrival_date TIMESTAMPTZ,
    departure_date TIMESTAMPTZ CHECK (departure_date IS NULL OR departure_date >= arrival_date),
    budget DECIMAL(10,2) CHECK (budget IS NULL OR budget >= 0),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Створення індексів
CREATE INDEX IF NOT EXISTS idx_locations_travel_plan_id ON locations(travel_plan_id);
CREATE INDEX IF NOT EXISTS idx_travel_plans_is_public ON travel_plans(is_public);
