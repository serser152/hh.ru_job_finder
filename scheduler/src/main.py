#!/usr/bin/env python
# coding: utf-8

import requests
import pandas as pd
import json
from time import sleep
from pytz import utc

from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor



def grab_hh(phone, password, request):

    res = requests.post('http://localhost:8000/find_vacancies', 
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
        res = requests.post('http://localhost:8000/find_vacancies', 
                        json={
                          "phone": phone,

                            "password": password,
                          "request": request
                        })
        max_try -= 1

    d=res.json()
    df = pd.DataFrame(json.loads(d))
    df['dt']=pd.to_datetime(df.dt, unit='ms')

    df.to_sql('hh_ds',con='postgresql://postgres:postgres@localhost:5433/public', if_exists='append', index=False)


    # grab new vac_ids
    df2 = pd.read_sql('''select vac_id from hh_ds_last_values where vac_id not in (select vac_id from vacancy_descriptions)''', con='postgresql://postgres:postgres@localhost:5433/public')

    vac_ids = df2.vac_id.to_list()

    res = requests.post('http://localhost:8000/get_vacancy_descriptions', 
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
        res = requests.post('http://localhost:8000/get_vacancy_descriptions', 
                        json={
                          "phone": phone,

                            "password": password,
                          "vacancy_ids": vac_ids
                        })
        max_try -= 1


    d=res.json()
    df = pd.DataFrame(json.loads(d))

    df.to_sql('vacancy_descriptions',con='postgresql://postgres:postgres@localhost:5433/public', if_exists='append', index=False)


def grab():
    print('grab job started')
    grab_hh('92001231234', '123', 'data science')


if __name__ == '__main__':
    print('Running')
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    }
    executors = {
        'processpool': ProcessPoolExecutor(5)
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }

    scheduler = BlockingScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)
    scheduler.add_job(grab,'cron', hour='22', minute='00')
    scheduler.start()

