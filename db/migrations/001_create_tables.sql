-- Створення таблиці travel_plans (оновлено для Lab 8: JSONB)
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
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Нове поле для зберігання локацій (Lab 8)
    locations JSONB NOT NULL DEFAULT '[]'::jsonb
);

-- Таблиця locations видалена, оскільки дані перенесені в travel_plans.locations

-- Створення індексів
CREATE INDEX IF NOT EXISTS idx_travel_plans_is_public ON travel_plans(is_public);
-- GIN індекс для ефективного пошуку всередині JSONB (опціонально)
CREATE INDEX IF NOT EXISTS idx_travel_plans_locations ON travel_plans USING GIN (locations);
