-- create tables
CREATE TABLE if not exists  public.vacancies (
    title text,
    dt timestamp without time zone,
    vac_id character varying,
    site character varying(100) DEFAULT 'hh.ru'::character varying,
    status character varying,
    link text
);

CREATE TABLE if not exists  public.vacancy_descriptions (
    vacancy_id serial primary key,
    vac_id character varying,
    vac_title text,
    vac_company text,
    vac_salary text,
    vac_exp text,
    vac_emp text,
    vac_hiring_format text,
    vac_working_hours text,
    vac_work_format text,
    vac_descr text,
    site character varying(100) DEFAULT 'hh.ru'::character varying
);

CREATE TABLE if not exists  public.vacancy_skills (
    vac_id character varying,
    site text,
    skill text
);

CREATE TABLE if not exists  public.searches (
    request text,
    phone text,
    password text,
    site text,
    enabled boolean
);

insert into public.searches (request, phone, password, site, enabled)
values ('data science','9061234567','pass123','zarplata.ru',false), ('data science','9061234567','pass123','hh.ru', false);



create table if not exists resume (
resume_id serial primary key,
resume text
)

create table if not exists resume_skills (
    resume_id int references resume(resume_id),
    skill varchar(100)
)

create table if not exists vacancy_resume_match (
    vacancy_id int references vacancy_descriptions(vacancy_id),
    resume_id int references resume(resume_id),
    metric float not null
)


--create views
CREATE OR REPLACE VIEW public.vacancies_start_end_date AS
 WITH c1 AS (
         SELECT max(hd2.dt) AS mdt
           FROM public.vacancies hd2
        ), c11 AS (
         SELECT min(hd2.dt) AS mdt
           FROM public.vacancies hd2
        ), c2 AS (
         SELECT hd.vac_id,
                hd.site,
            min(hd.dt) AS start_dt,
            max(hd.dt) AS end_dt
           FROM public.vacancies hd
          GROUP BY hd.vac_id, hd.site
          ORDER BY hd.vac_id
        ), c3 AS (
         SELECT c2.vac_id, c2.site,
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
    site,
    start_dt,
    end_dt
   FROM c3
  WHERE ((vac_id IS NOT NULL) AND (start_dt IS NOT NULL) AND (end_dt IS NOT NULL));

CREATE OR REPLACE VIEW public.closed_vac_descriptions AS
 SELECT vsed.end_dt,
    (vsed.end_dt - vsed.start_dt) AS "dt_diff",
    vd.vac_id,
    vd.vac_title,
    vd.vac_company,
    vd.vac_salary,
    vd.vac_exp,
    vd.vac_emp,
    vd.vac_hiring_format,
    vd.vac_working_hours,
    vd.vac_work_format,
    vd.vac_descr
   FROM public.vacancies_start_end_date vsed
     JOIN public.vacancy_descriptions vd ON ((vsed.vac_id = vd.vac_id) and (vsed.site = vd.site))
  ORDER BY vsed.end_dt DESC;


CREATE OR REPLACE VIEW public.vacancies_last_values AS
 SELECT title,
    dt,
    hd2.vac_id,
    hd2.site,
    hd2.status,
    link,
    h2.vac_company,
    h2.vac_salary,
    h2.vac_exp,
    h2.vac_emp,
    h2.vac_hiring_format,
    h2.vac_working_hours,
    h2.vac_work_format,
    h2.vac_descr
   FROM public.vacancies hd2
left join public.vacancy_descriptions h2 on (hd2.vac_id = h2.vac_id and hd2.site = h2.site)
  WHERE ((dt)::date = ( SELECT max((hd.dt)::date) AS max
           FROM public.vacancies hd));



CREATE OR REPLACE VIEW public.vacancies_last_money_hist AS
 WITH cte1 AS (
         SELECT hdlv.vac_salary as money,
            regexp_replace(replace(hdlv.vac_salary, '000'::text, ''::text), '(\d+)\s+(\d+)'::text, '\1\2'::text, 'g'::text) AS money2
           FROM public.vacancies_last_values hdlv
          WHERE (hdlv.vac_salary ~~ '%₽%'::text)
        ), cte2 AS (
         SELECT cte1.money2,
            (regexp_match(cte1.money2, '\d+'::text))::integer[] AS money_arr
           FROM cte1
        )
 SELECT money_arr[1] AS money_arr
   FROM cte2;



CREATE OR REPLACE VIEW public.last_vacancies_with_skills AS
 SELECT vs.skill,
    h1.title,
    h1.dt,
    h1.link,
    vd.*
   FROM public.vacancies_last_values h1
   JOIN public.vacancy_skills vs ON (
        ((vs.vac_id)::text = (h1.vac_id)::text) and
        ((vs.site)::text = (h1.site)::text))
   JOIN public.vacancy_descriptions vd ON (
        ((vd.vac_id)::text = (h1.vac_id)::text) and
        (((vd.site)::text = (h1.site)::text)))


