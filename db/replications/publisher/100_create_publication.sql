-- Створення publication для логічної реплікації
DROP PUBLICATION IF EXISTS travel_planner_pub;
CREATE PUBLICATION travel_planner_pub FOR ALL TABLES;

-- Перевірка publication
SELECT * FROM pg_publication WHERE pubname = 'travel_planner_pub';
