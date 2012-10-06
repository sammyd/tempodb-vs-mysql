-- Create the database
CREATE DATABASE IF NOT EXISTS timeseries;

USE timeseries;

-- Create the table
CREATE TABLE testSeries (
    timestamp TIMESTAMP,
    value1 DOUBLE,
    value2 INT
);
