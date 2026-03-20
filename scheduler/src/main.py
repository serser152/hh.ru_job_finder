#!/usr/bin/env python
# coding: utf-8

import requests
import pandas as pd
import json
from time import sleep
from pytz import utc, timezone
import datetime
from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor



def grab_hh(phone, password, request):
    phone = str(phone)
    con = 'postgresql://postgres:postgres@postgres:5432/public'
    res = requests.post('http://hh_grabber:8000/find_vacancies', 
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
        res = requests.post('http://hh_grabber:8000/find_vacancies', 
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
    where vac_id not in (select vac_id from vacancy_descriptions where site = 'hh.ru')
    and site = 'hh.ru' 
    ''', con=con)

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

    df.to_sql('vacancy_descriptions',con=con, if_exists='append', index=False)


def grab_zp(phone, password, request):

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


def grab():
    print('grab job started')
    con = 'postgresql://postgres:postgres@postgres:5432/public'
    df = pd.read_sql('''select * from searches''', con=con)
    for i,row in df.iterrows():
        if row.site == 'hh.ru':
            grab_hh(row.phone, row.password, row.request)
        elif row.site == 'zarplata.ru':
            grab_zp(row.phone, row.password, row.request)


if __name__ == '__main__':
    print('Running')
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    }
    executors = {
        'default': ProcessPoolExecutor(5)
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }

    scheduler = BlockingScheduler(
        jobstores=jobstores, 
        executors=executors, 
        job_defaults=job_defaults,
        timezone= timezone('Europe/Moscow'))
    scheduler.remove_all_jobs()
    scheduler.add_job(grab,'cron', hour='23', minute='49')
    print('sheduler started ',datetime.datetime.now())
    scheduler.start()

