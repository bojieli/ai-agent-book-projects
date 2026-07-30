-- 实验 5-10 ERP Agent —— 书中要求的 PostgreSQL schema（两张表）。
--
-- 本仓库的可运行演示用 SQLite（零依赖、可离线复现，见 seed.py / demo.py）；
-- 这份 DDL 给出书中原文的 PostgreSQL 版本，方便迁移到真实 Postgres 环境。
-- 两种方言的表结构一致，差异主要在日期函数：
--   SQLite:      strftime('%Y','now')        julianday(a)-julianday(b)   date('now','-1 year')
--   PostgreSQL:  EXTRACT(YEAR FROM now())     (a::date - b::date)         now() - interval '1 year'
--
-- 用法（需本机有 PostgreSQL）：
--   createdb erp
--   psql erp -f schema_postgres.sql

DROP TABLE IF EXISTS salaries;
DROP TABLE IF EXISTS employees;

-- 员工表：ID、姓名、部门、级别（数字越大越高）、入职日期、离职日期（NULL = 在职）
CREATE TABLE employees (
    emp_id      INTEGER     PRIMARY KEY,
    name        TEXT        NOT NULL,
    department  TEXT        NOT NULL,
    level       INTEGER     NOT NULL,
    hire_date   DATE        NOT NULL,
    leave_date  DATE                     -- NULL 表示在职
);

-- 工资表：员工ID、发薪日期（每月一条，取当月 1 号）、当月工资
CREATE TABLE salaries (
    emp_id      INTEGER     NOT NULL REFERENCES employees(emp_id),
    pay_date    DATE        NOT NULL,     -- 每月一条，如 2025-03-01
    salary      INTEGER     NOT NULL,
    PRIMARY KEY (emp_id, pay_date)
);

CREATE INDEX idx_salaries_pay_date ON salaries (pay_date);
