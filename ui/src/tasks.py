#!/usr/bin/env python
# coding: utf-8
"""Шаблон для задач celery"""
import json
from time import sleep
from io import StringIO
import psycopg2
import pandas as pd
import requests
from celery import Celery

CON = 'postgresql://postgres:postgres@postgres:5432/public'

app = Celery('tasks',
    backend='redis://redis:6379/0',
    broker='amqp://admin:secure_password@rabbitmq//')

def get_active_searches():
    """get active searches"""
    df = pd.read_sql('select * from searches',CON)
    return df

def update_db_df(edited_df):
    """update db"""
    edited_df.to_sql('searches', con=CON, index=False, if_exists='replace')


def get_last_data():
    """get last data """
    df2 = pd.read_sql('''select * from hh_ds_last_values''', con=CON)
    return df2


def del_last_data():
    """del last data grabbed"""
    conn = psycopg2.connect(CON)
    cur = conn.cursor()
    cur.execute('''
    delete from hh_ds
     WHERE dt = (( SELECT max(hd.dt) AS max
           FROM hh_ds hd));''')
    conn.commit()
    conn.close()

def init_db():
    """init db"""
    conn = psycopg2.connect(CON)
    cur = conn.cursor()
    cur.execute('''

drop table if exists hh.ds;

CREATE TABLE public.hh_ds (
    title text NULL,
    company text NULL,
    status text NULL,
    dt timestamp NULL,
    expirience text NULL,
    "money" text NULL,
    remote text NULL,
    vac_title text NULL,
    vac_salary text NULL,
    vac_exp text NULL,
    vac_emp text NULL,
    vac_hiring_format text NULL,
    vac_working_hours text NULL,
    vac_work_format text NULL,
    vac_descr text NULL,
    vac_id varchar NULL,
    site varchar(100) NULL DEFAULT 'hh.ru'::character varying
);

drop table if exists searches;

CREATE TABLE public.searches (
    request text NULL,
    phone text NULL,
    "password" text NULL,
    site text NULL,
    enabled bool NULL
);

drop table if exists vacancy_descriptions;

CREATE TABLE public.vacancy_descriptions (
    vac_id varchar NULL,
    vac_title text NULL,
    vac_salary text NULL,
    vac_exp text NULL,
    vac_emp text NULL,
    vac_hiring_format text NULL,
    vac_working_hours text NULL,
    vac_work_format text NULL,
    vac_descr text NULL,
    site varchar(100) NULL DEFAULT 'hh.ru'::character varying
);
''')
    conn.commit()
    conn.close()


def grab_hh(phone, password, request):
    """grab hh"""
    phone = str(phone)
    print('first try')
    print(f''' phone = "{phone}", "{password}", "{request}"''')
    res = requests.post('http://hh_grabber:8000/find_vacancies',
                        json={
                          "phone": phone,
                          "password": password,
                          "request": request
                        })

    print('res=', res)
    max_try = 5

    while not res.ok:
        if max_try == 0:
            raise Exception('API max retries reached')
        #wait 1 min
        sleep(60)
        # request again
        res = requests.post('http://hh_grabber:8000/find_vacancies',
                        json={
                        "phone": phone,
                        "password": password,
                        "request": request
                        })
        max_try -= 1

    d = res.json()
    df = pd.DataFrame(json.loads(d))
    df['dt'] = pd.to_datetime(df.dt, unit='ms')

    df.to_sql('hh_ds', con=CON, if_exists='append', index=False)

    # grab new vac_ids
    df2 = pd.read_sql('''select vac_id from hh_ds_last_values
                         where vac_id not in (select vac_id from vacancy_descriptions)''',
                      con=CON)

    vac_ids = df2.vac_id.to_list()

    res = requests.post('http://hh_grabber:8000/get_vacancy_descriptions',
                    json={
                      "phone": phone,
                      "password": password,
                      "vacancy_ids": vac_ids
                    })

    max_try = 5
    while not res.ok:
        if max_try == 0:
            raise Exception('Request vac desriptions: API max retries reached')
        #wait 1 min
        sleep(60)
        # request again
        res = requests.post('http://hh_grabber:8000/get_vacancy_descriptions',
                        json={
                          "phone": phone,
                          "password": password,
                          "vacancy_ids": vac_ids
                        })
        max_try -= 1


    d=res.json()
    df = pd.DataFrame(json.loads(d))

    df.to_sql('vacancy_descriptions',con=CON, if_exists='append', index=False)

def grab_zp(phone, password, request):
    phone=str(phone)
    con = 'postgresql://postgres:postgres@postgres:5432/public'
    res = requests.post('http://zarplata_grabber:8000/find_vacancies',
                        json={
                          "phone": phone,
                          "password": password,
                          "request": request
                        })

    max_try = 5

    while not res.ok:
        if max_try == 0:
            raise Exception('API max retries reached')
        #wait 1 min
        sleep(60)
        # request again
        res = requests.post('http://zarplata_grabber:8000/find_vacancies',
                        json={
                          "phone": phone,
                          "password": password,
                          "request": request
                        })
        max_try -= 1

    d=res.json()
    df = pd.DataFrame(json.loads(d))
    df['dt']=pd.to_datetime(df.dt, unit='ms')

    df.to_sql('hh_ds',con=con, if_exists='append',index=False)


    # grab new vac_ids
    df2 = pd.read_sql('''select vac_id from hh_ds_last_values 
    where vac_id not in (select vac_id from vacancy_descriptions where site = 'zarplata.ru')
    and site = 'zarplata.ru' 
    ''', con=con)

    vac_ids = df2.vac_id.to_list()

    res = requests.post('http://zarplata_grabber:8000/get_vacancy_descriptions',
                    json={
                      "phone": phone,
                      "password": password,
                      "vacancy_ids": vac_ids
                    })

    max_try = 5
    while not res.ok:
        if max_try == 0:
            raise Exception('Request vac desriptions: API max retries reached')
        #wait 1 min
        sleep(60)
        # request again
        res = requests.post('http://zarplata_grabber:8000/get_vacancy_descriptions',
                        json={
                          "phone": phone,
                          "password": password,
                          "vacancy_ids": vac_ids
                        })
        max_try -= 1


    d=res.json()
    df = pd.DataFrame(json.loads(d))
    df.to_sql('vacancy_descriptions',con=con, if_exists='append', index=False)


@app.task(bind=True)
def grab(self, df):
    '''grab vacancies using sources from dataframe df'''
    df2=pd.read_json(StringIO(df))
    print('grab job started')
    self.update_state(state='PROGRESS', meta={'done': 0})
    for i,row in df2.iterrows():
        # check if enabled
        if not row.enabled:
            continue
        if row.site == 'hh.ru':
            print('grab hh', row.request)
            grab_hh(row.phone, row.password, row.request)
        elif row.site == 'zarplata.ru':
            print('grab zp', row.request)
            grab_zp(row.phone, row.password, row.request)

        self.update_state(state='PROGRESS', meta={'done': 100.0*i/len(df2)})
    return 'DONE'
    #self.update_state(state='SUCCESS', meta={'done': 100.0 * i / len(df2)})


@app.task(bind=True)
def grab2(self,df):
    """grab vacancies test task"""
    df2=pd.read_json(StringIO(df))
    print(df2)
    self.update_state(state='PROGRESS', meta={'done': 0})
    sleep(10)
    self.update_state(state='PROGRESS', meta={'done': 25})
    sleep(10)
    self.update_state(state='PROGRESS', meta={'done': 50})
    sleep(10)
    self.update_state(state='PROGRESS', meta={'done': 75})
    sleep(10)
    self.update_state(state='PROGRESS', meta={'done': 100})
    return [{'request': 123}]
