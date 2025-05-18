-- Script DBeaver para crear la tabla `prefarmdb`

CREATE TABLE IF NOT EXISTS prefarmdb (
    time DATE PRIMARY KEY,
    amount_xch NUMERIC(20,12) NOT NULL
);
