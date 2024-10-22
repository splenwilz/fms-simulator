-- Update the curr_date table
UPDATE curr_date SET curr_date = "2024-10-29" WHERE curr_date > 0;

-- Reset the simulator_state table to set days_passed (clicks) to 0
UPDATE simulator_state SET days_passed = 0 WHERE id = 1;

-- Delete from the animals table first to avoid foreign key constraint issues
DELETE FROM animals WHERE id >= 0;

-- Delete from the stock table
DELETE FROM stock WHERE id >= 0;

-- Now it's safe to delete from mobs and paddocks
DELETE FROM mobs WHERE id >= 0;
DELETE FROM paddocks WHERE id >= 0;

-- Insert default paddocks
INSERT INTO paddocks VALUES
    (1, "Stream 1", 1.22, 1500, 1.22*1500),
    (4, "Rear 1", 1.23, 2300, 1.23*2300),
    (2, "Rear 2", 1.15, 1900, 1.15*1900),
    (12, "Barn", 0.95, 1750, 0.95*1750),
	(13, "Test", NULL, NULL, NULL),
    (14, "Test Paddock 1", NULL, NULL, NULL),
    (15, "Test Paddock 2", NULL, NULL, NULL),
    (16, "Test Paddock 3", NULL, NULL, NULL),
    (17, "Test Paddock 4", NULL, NULL, NULL),
    (18, "Test Paddock 5", NULL, NULL, NULL);

-- Insert default mobs
INSERT INTO mobs VALUES
    (1,"Mob 1", 4),
    (7,"Mob 2", 1),
    (2,"Mob 3", 2);

-- Insert default stock data
INSERT INTO stock VALUES
    (1001, 1, '2022-07-25', 586.3),
    (1002, 2, '2023-08-22', 311.2),
    (1003, 7, '2023-09-17', 293),
    (1004, 1, '2022-08-16', 570.9),
    (1005, 2, '2023-11-01', 261.5),
    (1006, 7, '2023-09-26', 286.7),
    (1007, 1, '2022-08-24', 565.3),
    (1008, 7, '2023-09-03', 302.8),
    (1009, 7, '2023-09-24', 288.1),
    (1010, 1, '2022-09-09', 554.1),
    (1011, 2, '2023-08-07', 321.7),
    (1012, 2, '2023-08-13', 317.5),
    (1013, 1, '2022-09-14', 550.6),
    (1014, 7, '2023-09-20', 290.9),
    (1015, 7, '2023-09-10', 297.9),
    (1016, 1, '2022-10-30', 518.4),
    (1017, 2, '2023-07-16', 337.1),
    (1018, 2, '2023-07-15', 337.8),
    (1019, 7, '2023-10-06', 279.7),
    (1020, 1, '2022-08-27', 563.2),
    (1021, 7, '2023-09-10', 297.9),
    (1022, 1, '2022-09-30', 539.4),
    (1023, 2, '2023-07-15', 337.8),
    (1024, 1, '2022-08-24', 565.3),
    (1025, 1, '2022-09-03', 558.3),
    (1026, 7, '2023-09-24', 288.1);
