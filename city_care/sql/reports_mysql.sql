DROP FUNCTION IF EXISTS fn_report_resolution_hours;
CREATE FUNCTION fn_report_resolution_hours(created_at DATETIME, last_status_at DATETIME)
RETURNS INT
DETERMINISTIC
RETURN TIMESTAMPDIFF(HOUR, created_at, last_status_at);

DROP VIEW IF EXISTS vw_weekly_reports_by_status;
CREATE VIEW vw_weekly_reports_by_status AS
SELECT
    YEARWEEK(created_at, 1) AS week,
    status,
    COUNT(*) AS total
FROM core_reports_report
GROUP BY YEARWEEK(created_at, 1), status;
