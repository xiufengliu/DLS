CREATE TABLE essex_hourlyreading
(
  meterid integer NOT NULL,
  readtime timestamp without time zone NOT NULL,
  reading double precision,
  activity double precision,
  temperature double precision,
  holiday integer,
  CONSTRAINT essex_hourlyreading_pkey PRIMARY KEY (meterid, readtime)
);

DROP TABLE IF EXISTS essex_meters cascade;
CREATE TABLE public.essex_meters
(
  meterid integer NOT NULL,
  meternumber character varying,
  customerpremisenumber integer,
  streetnumber integer,
  address character varying,
  connectdate timestamp without time zone,
  disconnectdate timestamp without time zone,
  peakkw double precision,
  volts integer,
  phase integer,
  areatown character varying,
  enabled integer,
  feeder character varying,
  pointx integer,
  pointy integer,
  transformerid character varying,
  lat double precision,
  lon double precision,
  pool_state_id integer,
  fsa_code integer,
  da_id_2011 integer,
  da_id_2006 integer,
  property_type_id integer,
  geom geometry(Point,4326),
  CONSTRAINT essex_meters_pkey PRIMARY KEY (meterid)
);

DROP TABLE IF EXISTS essex_neighborhood CASCADE;
CREATE TABLE essex_neighborhood
(
  id character varying NOT NULL,
  name character varying NOT NULL,
  geom geometry(Polygon,4326),
  CONSTRAINT essex_neighborhood_pkey PRIMARY KEY (id)
);

DROP TABLE IF EXISTS essex_segment_types CASCADE;
CREATE TABLE essex_segment_types(
  id integer primary key,
  "name"  character varying
);
INSERT INTO essex_segment_types VALUES (1, 'By manual');
INSERT INTO essex_segment_types VALUES (2, 'By soci-characteristics');
INSERT INTO essex_segment_types VALUES (3, 'By clustering');



DROP TABLE IF EXISTS essex_consumption_patterns CASCADE;
CREATE TABLE essex_consumption_patterns
(
  "name" character varying,
  id character varying NOT NULL,
  readings float8[],
  seg_type INTEGER  REFERENCES essex_segment_types(id)
);
CREATE INDEX idx_essex_consumption_patterns_name ON essex_consumption_patterns USING btree (name) ;


DROP TABLE IF EXISTS essex_job_que CASCADE ;
CREATE TABLE essex_job_que(
id serial primary key,
name character varying ,
script TEXT,
next_execute_time timestamp default now()-interval'1hours',
seg_type INTEGER REFERENCES essex_segment_types(id)
);
INSERT INTO essex_job_que(name, seg_type, script) VALUES ('Manual-Job', 1, 'DELETE FROM essex_consumption_patterns WHERE seg_type=1;INSERT INTO essex_consumption_patterns(name, id, readings, seg_type) SELECT r.name, r.id, array_agg(r.reading ORDER BY r.hour), 1 FROM (SELECT D.name, D.id, extract(hour FROM readtime) AS hour, avg(reading) as reading FROM essex_hourlyreading C, (SELECT A.name, A.id, B.meterid FROM essex_neighborhood A, essex_meters B WHERE ST_Contains(A.geom, B.geom)) D WHERE C.meterid=D.meterid GROUP BY 1,2,3) AS r GROUP BY 1, 2');
INSERT INTO essex_job_que(name, seg_type, script) VALUES ('Clustering-Job', 3,
'DROP TABLE IF EXISTS essex_consumption_patterns_forclustering;
CREATE TABLE essex_consumption_patterns_forclustering AS
SELECT meterid, array_agg(reading order by hour) AS readings, -1 AS clusterid FROM
(SELECT meterid, extract(hour FROM readtime) AS hour, avg(reading) AS reading
FROM essex_hourlyreading group by 1,2 order by 1,2) A group by 1;
ALTER TABLE essex_consumption_patterns_forclustering add CONSTRAINT essex_consumption_patterns_forclustering_pk PRIMARY KEY (meterid);
DROP TABLE IF EXISTS essex_consumption_patterns_forclustering_results;
CREATE TABLE essex_consumption_patterns_forclustering_results AS
SELECT * FROM madlib.kmeanspp(''essex_consumption_patterns_forclustering'',
                               ''readings'',
                               5,
                               ''madlib.squared_dist_norm2'',
                               ''madlib.avg'',
                               20,
                               0.001
                             );
UPDATE essex_consumption_patterns_forclustering set clusterid= (madlib.closest_column(centroids, readings)).column_id from essex_consumption_patterns_forclustering_results;
DELETE FROM essex_consumption_patterns WHERE seg_type=3;
INSERT INTO essex_consumption_patterns(name, id, readings, seg_type)
SELECT ''Clustering-1'',
(madlib.closest_column(centroids, unnest_result)).column_id as cluster_id,
cent.unnest_result as centroid,
3
FROM (SELECT (madlib.array_unnest_2d_to_1d(centroids)).*
FROM essex_consumption_patterns_forclustering_results) as cent, essex_consumption_patterns_forclustering_results
ORDER BY 1');

