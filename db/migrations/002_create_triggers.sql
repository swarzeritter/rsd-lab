-- Створення функції для оновлення updated_at та version
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Створення тригера для travel_plans
DROP TRIGGER IF EXISTS update_travel_plans_modtime ON travel_plans;
CREATE TRIGGER update_travel_plans_modtime
BEFORE UPDATE ON travel_plans
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
