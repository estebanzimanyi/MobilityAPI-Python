-- ============================================================================
-- ACTIVITY 2: VESSELS - Complete Processing Pipeline
-- Based on Assignment 2 solutions from ULB
-- ============================================================================
SET DATESTYLE = 'ISO, DMY';
 -- 1. Create the MobilityDB extension if not exists
CREATE EXTENSION IF NOT EXISTS MobilityDB CASCADE;

-- 2. Create the raw AIS input table (based on PDF page 2)
DROP TABLE IF EXISTS AISInput;
CREATE TABLE AISInput(
    T timestamp,
    TypeOfMobile varchar(50),
    MMSI integer,
    Latitude float,
    Longitude float,
    NavigationalStatus varchar(60),
    ROT float,
    SOG float,
    COG float,
    Heading integer,
    IMO varchar(50),
    Callsign varchar(50),
    Name varchar(100),
    ShipType varchar(50),
    CargoType varchar(100),
    Width float,
    Length float,
    TypeOfPositionFixingDevice varchar(50),
    Draught float,
    Destination varchar(50),
    ETA varchar(50),
    DataSourceType varchar(50),
    SizeA float,
    SizeB float,
    SizeC float,
    SizeD float
);

-- 3. Load data from CSV (adjust path as needed)
-- For Docker: '/tmp/aisdk-2024-08-07.csv'
-- For local: '/your/path/aisdk-2024-08-07.csv'
COPY AISInput(T, TypeOfMobile, MMSI, Latitude, Longitude, NavigationalStatus, 
     ROT, SOG, COG, Heading, IMO, Callsign, Name, ShipType, CargoType, 
     Width, Length, TypeOfPositionFixingDevice, Draught, Destination, ETA, 
     DataSourceType, SizeA, SizeB, SizeC, SizeD)
FROM :data_csv_path DELIMITER  ',' CSV HEADER ;

-- ============================================================================
-- CLEANING PHASE (based on PDF page 7)
-- ============================================================================

-- 4. Add geometry column
ALTER TABLE AISInput ADD COLUMN Geom geometry(Point, 25832);

-- 5. Clean data and create geometry in one pass
UPDATE AISInput
SET
    -- Replace placeholders with NULL
    NavigationalStatus = CASE NavigationalStatus 
        WHEN 'Unknown value' THEN NULL 
        WHEN 'Undefined' THEN NULL 
        ELSE NavigationalStatus 
    END,
    IMO = CASE IMO WHEN 'Unknown' THEN NULL ELSE IMO END,
    ShipType = CASE ShipType WHEN 'Undefined' THEN NULL ELSE ShipType END,
    CargoType = CASE CargoType WHEN 'Undefined' THEN NULL ELSE CargoType END,
    TypeOfPositionFixingDevice = CASE TypeOfPositionFixingDevice 
        WHEN 'Undefined' THEN NULL 
        ELSE TypeOfPositionFixingDevice 
    END,
    Destination = CASE Destination 
        WHEN 'Unknown' THEN NULL 
        WHEN 'Undefined' THEN NULL 
        ELSE Destination 
    END,
    Name = CASE Name WHEN 'Unknown' THEN NULL ELSE Name END,
    Callsign = CASE Callsign WHEN 'Unknown' THEN NULL ELSE Callsign END,
    -- Create geometry for points within Denmark zone (SRID 25832 bounds)
    Geom = ST_Transform(
        ST_SetSRID(ST_MakePoint(Longitude, Latitude), 4326), 
        25832
    )
WHERE 
    Latitude BETWEEN 40.18 AND 84.73 
    AND Longitude BETWEEN -16.1 AND 32.88
    AND SOG IS NOT NULL
    AND COG IS NOT NULL;

-- ============================================================================
-- DEDUPLICATION PHASE (based on PDF page 18, Option C)
-- ============================================================================

-- 6. Create filtered table with unique (MMSI, T) pairs
DROP TABLE IF EXISTS AISInputFiltered;
CREATE TABLE AISInputFiltered AS
SELECT DISTINCT ON (MMSI, T) 
    T, TypeOfMobile, MMSI, Latitude, Longitude, NavigationalStatus,
    ROT, SOG, COG, Heading, IMO, Callsign, Name, ShipType, CargoType,
    Width, Length, TypeOfPositionFixingDevice, Draught, Destination, ETA,
    DataSourceType, SizeA, SizeB, SizeC, SizeD, Geom
FROM AISInput
WHERE Geom IS NOT NULL
ORDER BY MMSI, T;

-- ============================================================================
-- TRAJECTORY GENERATION PHASE (based on PDF page 20)
-- ============================================================================

-- 7. Create Ships table with temporal sequences
DROP TABLE IF EXISTS Ships;
CREATE TABLE Ships AS
SELECT 
    MMSI,
    tgeompointseq(array_agg(tgeompoint(Geom, T) ORDER BY T)) AS Trip,
    tfloatseq(array_agg(tfloat(SOG, T) ORDER BY T) 
        FILTER (WHERE SOG IS NOT NULL)) AS SOG,
    tfloatseq(array_agg(tfloat(COG, T) ORDER BY T) 
        FILTER (WHERE COG IS NOT NULL)) AS COG,
    tfloatseq(array_agg(tfloat(Heading, T) ORDER BY T) 
        FILTER (WHERE Heading IS NOT NULL)) AS Heading,
    -- Static properties using MIN (works in standard PostgreSQL)
    MIN(Name) FILTER (WHERE Name IS NOT NULL) AS Name,
    MIN(IMO) FILTER (WHERE IMO IS NOT NULL) AS IMO,
    MIN(ShipType) FILTER (WHERE ShipType IS NOT NULL) AS ShipType,
    MIN(CargoType) FILTER (WHERE CargoType IS NOT NULL) AS CargoType,
    MIN(Destination) FILTER (WHERE Destination IS NOT NULL) AS Destination,
    MIN(Callsign) FILTER (WHERE Callsign IS NOT NULL) AS Callsign,
    MIN(NavigationalStatus) FILTER (WHERE NavigationalStatus IS NOT NULL) AS NavigationalStatus,
    MIN(TypeOfMobile) FILTER (WHERE TypeOfMobile IS NOT NULL) AS TypeOfMobile,
    MIN(Length) FILTER (WHERE Length IS NOT NULL) AS Length,
    MIN(Width) FILTER (WHERE Width IS NOT NULL) AS Width,
    MIN(Draught) FILTER (WHERE Draught IS NOT NULL) AS Draught
FROM AISInputFiltered
GROUP BY MMSI;

-- 8. Add trajectory geometry column for visualization (based on PDF page 20)
ALTER TABLE Ships ADD COLUMN Traj geometry;
UPDATE Ships SET Traj = trajectory(Trip);

-- ============================================================================
-- CLEANUP: Remove invalid trajectories (based on PDF page 23)
-- ============================================================================

-- 9. Remove trajectories with zero length or too long (>1500km = 1,500,000 meters)
DELETE FROM Ships 
WHERE length(Trip) = 0 OR length(Trip) >= 1500000;

-- 10. Remove trajectories where SOG doesn't match calculated speed (based on PDF page 24-25)
DELETE FROM Ships
WHERE 
    ABS(twavg(SOG) * 1.852 - twavg(speed(Trip)) * 3.6) IS NULL
    OR ABS(twavg(SOG) * 1.852 - twavg(speed(Trip)) * 3.6) > 100;

-- ============================================================================
-- EXPORT TO JSON (PostgreSQL JSON functions)
-- ============================================================================

-- 11. Create a view that formats data as JSON (ready for your API)

-- limited to trajectories that intersected ports rodby andPuttgarden (Germany) for memo reasons
-- First drop the old view/table if it exists
DROP TABLE IF EXISTS ships_json CASCADE;

-- Then create the filtered table using a CTE
CREATE TABLE ships_json AS
WITH ShipsBelt AS (
    SELECT S.*
    FROM Ships S,
         ST_MakeEnvelope(640730, 6058230, 654100, 6042487, 25832) AS belt
    WHERE eintersects(S.Trip, belt)
)
SELECT 
    MMSI,
    jsonb_build_object(
        'mmsi', MMSI,
        'trajectory', asMFJSON(Trip),
        'sog', asMFJSON(SOG),
        'cog', asMFJSON(COG),
        'heading', asMFJSON(Heading),
        'properties', jsonb_build_object(
            'Name', Name,
            'IMO', IMO,
            'ShipType', ShipType,
            'Destination', Destination
        )
    ) AS json_data
FROM ShipsBelt;
-- ============================================================================
-- HELPER QUERIES FOR SPECIFIC PORTS (based on PDF pages 26-35)
-- ============================================================================

-- 12. Port of Rodby (Denmark)
-- Coordinates from PDF: 652129 6059729
-- Envelope: ST_MakeEnvelope(651135, 6058230, 651422, 6058548, 25832)

-- 13. Port of Puttgarden (Germany)
-- Envelope: ST_MakeEnvelope(644339, 6042108, 644896, 6042487, 25832)

-- 14. Find ships traveling between Rodby and Puttgarden
-- SELECT s.MMSI, s.Name, length(s.Trip)/1000 AS length_km
-- FROM Ships s
-- WHERE eintersects(s.Trip, ST_MakeEnvelope(651135, 6058230, 651422, 6058548, 25832))
--   AND eintersects(s.Trip, ST_MakeEnvelope(644339, 6042108, 644896, 6042487, 25832));