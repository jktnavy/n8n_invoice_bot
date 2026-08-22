-- Replace the placeholder password outside Git before running.
-- Do not use MySQL root as the runtime application user.

CREATE USER IF NOT EXISTS 'invoice_bot_v2'@'localhost'
  IDENTIFIED BY 'CHANGE_ME_OUTSIDE_GIT';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
ON invoice_bot_v2.*
TO 'invoice_bot_v2'@'localhost';

FLUSH PRIVILEGES;

