-- 本地 Core 只复用 PostgreSQL 实例，不混用两个项目的数据库。
-- 脚本由官方镜像在空数据卷首次启动时执行。

SELECT 'CREATE DATABASE jiyaojun'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'jiyaojun')
\gexec

SELECT 'CREATE DATABASE safety'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'safety')
\gexec
