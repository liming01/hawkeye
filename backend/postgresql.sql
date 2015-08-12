create database hackday;

\c hackday

drop table IF EXISTS hosts;
create table hosts(id SERIAL PRIMARY KEY, host varchar(256));

drop table IF EXISTS monitor_meta;
create table monitor_meta (id SERIAL, enable boolean, interval int, host smallint[], process_regexp varchar(256), memory boolean, cpu boolean, network boolean, disk boolean);

drop table IF EXISTS collect_data;
create table collect_data(rule_id integer, time timestamp, host smallint, pid int, connid int, cmdid bigint, memory bigint, cpu smallint, network bigint, disk bigint, mem_total bigint, mem_free bigint);

--create trigger to monitor on table monitor_meta
CREATE PROCEDURAL LANGUAGE plpgsql;

drop FUNCTION IF EXISTS notify_trigger1() cascade;
CREATE FUNCTION notify_trigger1() RETURNS trigger AS $$
DECLARE
BEGIN
     -- TG_TABLE_NAME is the name of the table who's trigger called this function
      -- TG_OP is the operation that triggered this function: INSERT, UPDATE or DELETE.
       --execute 'NOTIFY ' || TG_TABLE_NAME || ', '||TG_OP || '_'|| OLD.id;
       PERFORM pg_notify(TG_TABLE_NAME, TG_OP|| '_' || CAST(NEW.id AS text));
     return new;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS notify_trigger1 ON monitor_meta CASCADE;
CREATE TRIGGER table_trigger1 AFTER insert or update on monitor_meta FOR EACH ROW EXECUTE procedure notify_trigger1();


drop FUNCTION notify_trigger2() cascade;
CREATE FUNCTION notify_trigger2() RETURNS trigger AS $$
DECLARE
BEGIN
     -- TG_TABLE_NAME is the name of the table who's trigger called this function
      -- TG_OP is the operation that triggered this function: INSERT, UPDATE or DELETE.
       --execute 'NOTIFY ' || TG_TABLE_NAME || ', '||TG_OP || '_'|| OLD.id;
       PERFORM pg_notify(TG_TABLE_NAME, TG_OP|| '_' || CAST(OLD.id AS text));
     return old;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS notify_trigger2 ON monitor_meta CASCADE;
CREATE TRIGGER table_trigger2 BEFORE delete on monitor_meta FOR EACH ROW EXECUTE procedure notify_trigger2();


INSERT INTO monitor_meta(enable, interval, host, process_regexp, memory, cpu, network, disk) VALUES( TRUE,3,'{-1}','*',TRUE,FALSE,FALSE,FALSE);
INSERT INTO monitor_meta(enable, interval, host, process_regexp, memory, cpu, network, disk) VALUES( TRUE,3,'{1,2}','*',TRUE,FALSE,FALSE,FALSE);

UPDATE monitor_meta SET cpu=TRUE WHERE id=1; 

DELETE FROM monitor_meta;
