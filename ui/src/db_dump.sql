--
-- PostgreSQL database dump
--

-- Dumped from database version 17.9 (Debian 17.9-1.pgdg13+1)
-- Dumped by pg_dump version 17.6 (Debian 17.6-0+deb13u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: hh_ds; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hh_ds (
    title text,
    company text,
    status text,
    dt timestamp without time zone,
    expirience text,
    money text,
    remote text,
    vac_id character varying,
    site character varying(100) DEFAULT 'hh.ru'::character varying,
    link text
);


ALTER TABLE public.hh_ds OWNER TO postgres;

--
-- Name: vacancies_start_end_date; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.vacancies_start_end_date AS
 WITH c1 AS (
         SELECT max(hd2.dt) AS mdt
           FROM public.hh_ds hd2
        ), c11 AS (
         SELECT min(hd2.dt) AS mdt
           FROM public.hh_ds hd2
        ), c2 AS (
         SELECT hd.vac_id,
            min(hd.dt) AS start_dt,
            max(hd.dt) AS end_dt
           FROM public.hh_ds hd
          GROUP BY hd.vac_id
          ORDER BY hd.vac_id
        ), c3 AS (
         SELECT c2.vac_id,
                CASE
                    WHEN (c2.start_dt = c11.mdt) THEN NULL::timestamp without time zone
                    ELSE c2.start_dt
                END AS start_dt,
                CASE
                    WHEN (c2.end_dt = c1.mdt) THEN NULL::timestamp without time zone
                    ELSE c2.end_dt
                END AS end_dt
           FROM c1,
            c2,
            c11
        )
 SELECT vac_id,
    start_dt,
    end_dt
   FROM c3
  WHERE ((vac_id IS NOT NULL) AND (start_dt IS NOT NULL) AND (end_dt IS NOT NULL));


ALTER VIEW public.vacancies_start_end_date OWNER TO postgres;

--
-- Name: vacancy_descriptions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vacancy_descriptions (
    vac_id character varying,
    vac_title text,
    vac_salary text,
    vac_exp text,
    vac_emp text,
    vac_hiring_format text,
    vac_working_hours text,
    vac_work_format text,
    vac_descr text,
    site character varying(100) DEFAULT 'hh.ru'::character varying
);


ALTER TABLE public.vacancy_descriptions OWNER TO postgres;

--
-- Name: closed_vac_descriptions; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.closed_vac_descriptions AS
 SELECT vsed.end_dt,
    (vsed.end_dt - vsed.start_dt) AS "?column?",
    vd.vac_id,
    vd.vac_title,
    vd.vac_salary,
    vd.vac_exp,
    vd.vac_emp,
    vd.vac_hiring_format,
    vd.vac_working_hours,
    vd.vac_work_format,
    vd.vac_descr
   FROM (public.vacancies_start_end_date vsed
     JOIN public.vacancy_descriptions vd ON (((vsed.vac_id)::text = (vd.vac_id)::text)))
  ORDER BY vsed.end_dt DESC;


ALTER VIEW public.closed_vac_descriptions OWNER TO postgres;

--
-- Name: hh_ds_last_values; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.hh_ds_last_values AS
 SELECT title,
    company,
    status,
    dt,
    expirience,
    money,
    remote,
    vac_id,
    site,
    link
   FROM public.hh_ds hd2
  WHERE ((dt)::date = ( SELECT max((hd.dt)::date) AS max
           FROM public.hh_ds hd));


ALTER VIEW public.hh_ds_last_values OWNER TO postgres;

--
-- Name: hh_ds_last_money_hist; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.hh_ds_last_money_hist AS
 WITH cte1 AS (
         SELECT hdlv.money,
            regexp_replace(replace(hdlv.money, '000'::text, ''::text), '(\d+)\s+(\d+)'::text, '\1\2'::text, 'g'::text) AS money2
           FROM public.hh_ds_last_values hdlv
          WHERE (hdlv.money ~~ '%₽%'::text)
        ), cte2 AS (
         SELECT cte1.money2,
            (regexp_match(cte1.money2, '\d+'::text))::integer[] AS money_arr
           FROM cte1
        )
 SELECT money_arr[1] AS money_arr
   FROM cte2;


ALTER VIEW public.hh_ds_last_money_hist OWNER TO postgres;

--
-- Name: searches; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.searches (
    request text,
    phone text,
    password text,
    site text,
    enabled boolean
);


ALTER TABLE public.searches OWNER TO postgres;


insert into public.searches (request, phone, password, site, enabled) 
values ('data science','9061234567','pass123','zarplata.ru',false), ('data science','9061234567','pass123','hh.ru', false);





