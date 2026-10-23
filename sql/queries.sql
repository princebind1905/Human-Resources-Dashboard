-- =====================================================================
-- HR Analytics Dashboard — reference SQL
-- These are the exact queries app.py runs against db/hr.db (table: employees).
-- Filter placeholders (:department, :state, :gender, :education) are bound
-- as parameters in app.py; shown here as commented examples so the file
-- is runnable as-is in any SQLite client.
-- =====================================================================

-- 1. Headline KPIs -----------------------------------------------------
SELECT
    COUNT(*) AS total_ever,
    SUM(CASE WHEN Status = 'Active' THEN 1 ELSE 0 END) AS active,
    SUM(CASE WHEN Status = 'Terminated' THEN 1 ELSE 0 END) AS terminated,
    ROUND(AVG("Tenure (Years)"), 1) AS avg_tenure,
    ROUND(100.0 * SUM(CASE WHEN Status = 'Terminated' THEN 1 ELSE 0 END) / COUNT(*), 1) AS attrition_rate_pct
FROM employees;

-- 2. Hiring vs termination trend by year --------------------------------
SELECT strftime('%Y', Hiredate) AS yr, COUNT(*) AS hires
FROM employees
GROUP BY yr
ORDER BY yr;

SELECT strftime('%Y', Termdate) AS yr, COUNT(*) AS terminations
FROM employees
WHERE Termdate IS NOT NULL
GROUP BY yr
ORDER BY yr;

-- 3. Headcount by department (active vs terminated) ---------------------
SELECT
    Department,
    SUM(CASE WHEN Status = 'Active' THEN 1 ELSE 0 END) AS active,
    SUM(CASE WHEN Status = 'Terminated' THEN 1 ELSE 0 END) AS terminated,
    COUNT(*) AS total
FROM employees
GROUP BY Department
ORDER BY total DESC;

-- 4. Headcount by state (map / list) -------------------------------------
SELECT State, COUNT(*) AS headcount
FROM employees
GROUP BY State
ORDER BY headcount DESC;

-- 5. HQ vs Branch split ---------------------------------------------------
SELECT "Location Type", COUNT(*) AS headcount
FROM employees
GROUP BY "Location Type";

-- 6. Gender split -----------------------------------------------------
SELECT Gender, COUNT(*) AS headcount
FROM employees
GROUP BY Gender;

-- 7. Education x Age Group matrix ----------------------------------------
SELECT "Age Group", "Education Level", COUNT(*) AS headcount
FROM employees
GROUP BY "Age Group", "Education Level";

-- 8. Education x Performance matrix ---------------------------------------
SELECT "Performance Rating", "Education Level", COUNT(*) AS headcount
FROM employees
GROUP BY "Performance Rating", "Education Level";

-- 9. Average salary by Education x Gender ----------------------------------
SELECT "Education Level", Gender, ROUND(AVG(Salary), 0) AS avg_salary
FROM employees
GROUP BY "Education Level", Gender;

-- 10. Age vs Salary by job title (averaged, used for the scatter plot) -----
SELECT "Job Title", Age, ROUND(AVG(Salary), 0) AS avg_salary
FROM employees
GROUP BY "Job Title", Age;

-- 11. Pay-equity gap check (extra: flags >5% gap within an education level) -
SELECT
    "Education Level",
    ROUND(AVG(CASE WHEN Gender = 'Male' THEN Salary END), 0)   AS male_avg,
    ROUND(AVG(CASE WHEN Gender = 'Female' THEN Salary END), 0) AS female_avg,
    ROUND(
        100.0 * (
            AVG(CASE WHEN Gender = 'Male' THEN Salary END) -
            AVG(CASE WHEN Gender = 'Female' THEN Salary END)
        ) / AVG(CASE WHEN Gender = 'Male' THEN Salary END)
    , 1) AS pct_gap
FROM employees
GROUP BY "Education Level";

-- 12. Employee records (filterable, searchable, paginated) -----------------
-- app.py builds this dynamically with WHERE / LIKE / ORDER BY / LIMIT-OFFSET
-- depending on the sidebar filters and search box. Example:
SELECT
    Employee_ID, "Full Name", Department, "Job Title", Gender, Age,
    "Education Level", Salary, "Performance Rating", Status
FROM employees
-- WHERE Department = :department
--   AND State = :state
--   AND (:search = '' OR "Full Name" LIKE '%' || :search || '%')
ORDER BY Salary DESC
LIMIT 25 OFFSET 0;
