-- Summary of all recorded samples.
SELECT
    COUNT(*) AS sample_count,
    ROUND(AVG(rpm), 2) AS average_rpm,
    ROUND(MAX(rpm), 2) AS maximum_rpm,
    MIN(received_at_utc) AS first_sample_utc,
    MAX(received_at_utc) AS last_sample_utc
FROM readings;

-- Average RPM while the engine is running.
SELECT
    COUNT(*) AS running_sample_count,
    ROUND(AVG(rpm), 2) AS average_running_rpm
FROM readings
WHERE rpm > 0;

-- Ten samples with the highest RPM.
SELECT
    id,
    received_at_utc,
    rpm
FROM readings
ORDER BY rpm DESC, id ASC
LIMIT 10;