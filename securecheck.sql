use secure_check;

-- Create the flagged vehicles table
CREATE TABLE IF NOT EXISTS flagged_vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(20),
    reason VARCHAR(255),
    flagged_date DATE
);

-- Adding some test data so the alert works
INSERT INTO flagged_vehicles (vehicle_number, reason, flagged_date) VALUES
('AB1234', 'Repeat drug offender', '2026-01-15'),
('XY9999', 'Stolen vehicle', '2026-02-20');

select * from flagged_vehicles;

SELECT vehicle_number, COUNT(*) as stop_count 
FROM traffic_stops 
WHERE vehicle_number IS NOT NULL AND vehicle_number != ''
GROUP BY vehicle_number 
ORDER BY stop_count DESC 
LIMIT 10;

DELETE FROM flagged_vehicles WHERE id > 0;

INSERT INTO flagged_vehicles (vehicle_number, reason, flagged_date) VALUES
('WB63BB8305', 'Repeat drug offender', '2026-01-10'),
('UP76DY3473', 'Stolen vehicle', '2026-01-15'),
('RJ83PZ4441', 'Suspended license', '2026-02-01'),
('RJ76TI3807', 'Outstanding warrant', '2026-02-10'),
('DL75KZ7835', 'Repeat offender', '2026-03-01');