-- Створення subscription на Slave
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_subscription WHERE subname = 'travel_planner_sub') THEN
        CREATE SUBSCRIPTION travel_planner_sub
        CONNECTION 'host=postgres port=5432 user=repuser password=repuser dbname=travel_db'
        PUBLICATION travel_planner_pub;
        RAISE NOTICE 'Subscription created successfully';
    ELSE
        RAISE NOTICE 'Subscription already exists';
    END IF;
END
$$;

-- Перевірка статусу
SELECT subname, subenabled, subslotname FROM pg_subscription;

