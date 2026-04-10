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
import sqlalchemy




class ScrapingException(Exception):
    """ Scraping exception"""
    def __init__(self, msg):
        self.msg = msg
        super().__init__(self.msg)


CON = 'postgresql://postgres:postgres@postgres:5432/public'
MAX_RETRY = 0


app = Celery('tasks',
    backend='redis://redis:6379/0',
    broker='amqp://admin:secure_password@rabbitmq//')
#app = Celery('tasks',
#    backend='redis://localhost:6380/0',
#    broker='amqp://admin:secure_password@localhost:5673//')
#CON = 'postgresql://postgres:postgres@localhost:5433/public'


def get_active_searches():
    """get active searches"""
    df = pd.read_sql('select * from searches',CON)
    return df

def update_db_df(edited_df):
    """update db"""
    edited_df.to_sql('searches', con=CON, index=False, if_exists='replace')


def get_last_data():
    """get last data """
    df2 = pd.read_sql('''select h1.link, h2.* from vacancies_last_values h1
    join vacancy_descriptions h2 on h1.vac_id = h2.vac_id and h1.site = h2.site''', con=CON)
    return df2

def get_empty_descriptions_data():
    """get last data without parsed skills"""
    df2 = pd.read_sql('''select h2.* from vacancies_last_values h1
join vacancy_descriptions h2 on h1.vac_id = h2.vac_id
where h2.vac_id not in (select distinct vac_id from vacancy_skills)
and h2.vac_descr is not null
''', con=CON)
    return df2

def del_last_data():
    """del last data grabbed"""
    conn = psycopg2.connect(CON)
    cur = conn.cursor()
    cur.execute('''
    delete from vacancies
     WHERE dt = (( SELECT max(hd.dt) AS max
           FROM vacancies hd));''')
    conn.commit()
    conn.close()


def init_db():
    """init db"""
    conn = psycopg2.connect(CON)
    cur = conn.cursor()
    with open('db_dump.sql',encoding='utf-8') as f:
        sql = f.read()
    cur.execute(sql)
    conn.commit()
    conn.close()


def check_db():
    '''check database and initialize if required'''
    try:
        get_active_searches()
    except sqlalchemy.exc.NoSuchTableError:
        init_db()
    except psycopg2.errors.UndefinedTable:
        init_db()
    except pd.errors.DatabaseError:
        init_db()


def grab_new_vac_desc(site, phone, password, s = None):
    """
    grab new vacancies description
    """
    print(f'Get new vac description for {site}')
    phone = str(phone)
    df2 = pd.read_sql(f'''
    select vac_id from vacancies_last_values 
    where vac_id not in (select vac_id from vacancy_descriptions where site ='{site}')
    and site = '{site}' ''',
    con=CON)

    vac_ids = df2.vac_id.to_list()
    batch_size = 20
    steps = len(vac_ids)//batch_size
    for i in range(steps):
        batch = vac_ids[i*batch_size:(i+1)*batch_size]

        jsn={
            "site": site,
            "phone": phone,
            "password": password,
            "vacancy_ids": batch
        }
        res = requests.post('http://grabber:8000/get_vacancy_descriptions',
                        json=jsn, timeout=2400)

        max_try = MAX_RETRY
        while not res.ok:
            if max_try == 0:
                raise ScrapingException('Request vac desriptions: API max retries reached')
            #wait 1 min
            sleep(60)
            # request again
            res = requests.post('http://grabber:8000/get_vacancy_descriptions',
                            json=jsn, timeout=2400)
            max_try -= 1


        d=res.json()
        df = pd.DataFrame(json.loads(d))

        df.to_sql('vacancy_descriptions',con=CON, if_exists='append', index=False)
        print(f'step {i} of {steps} done')
        if s:
            s.update_state(state='PROGRESS', meta={'done': int(100.0*i/steps)})
        sleep(2)

def grab_site(site, phone, password, request):
    """grab vacancies"""
    phone = str(phone)
    print('first try')

    jsn={
          "site": site,
          "phone": phone,
          "password": password,
          "request": request
    }

    res = requests.post('http://grabber:8000/find_vacancies',
                    json=jsn, timeout=2400)

    max_try = MAX_RETRY

    while not res.ok:
        if max_try == 0:
            raise ScrapingException('API max retries reached')
        #wait 1 min
        sleep(60)
        # request again
        res = requests.post('http://grabber:8000/find_vacancies',
                    json=jsn, timeout=2400)
        max_try -= 1

    d = res.json()
    df = pd.DataFrame(json.loads(d))
    df['dt'] = pd.to_datetime(df.dt, unit='ms')

    df.to_sql('vacancies', con=CON, if_exists='append', index=False)
    grab_new_vac_desc(site, phone, password)


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
        print(f'grab {row.request} {row.site}')
        grab_site(row.site, row.phone, row.password, row.request)

        self.update_state(state='PROGRESS', meta={'done': 100.0*i/len(df2)})
    return 'DONE'
    #self.update_state(state='SUCCESS', meta={'done': 100.0 * i / len(df2)})


@app.task(bind=True)
def grab_description(self, df):
    '''grab vacancies using sources from dataframe df'''
    df2=pd.read_json(StringIO(df))
    print('grab job started')
    self.update_state(state='PROGRESS', meta={'done': 0})
    for i,row in df2.iterrows():
        # check if enabled
        if not row.enabled:
            continue
        print(f'grab new desc {i} ', row.request)
        grab_new_vac_desc(row.site, row.phone, row.password, self)

        #self.update_state(state='PROGRESS', meta={'done': int(100.0*i/len(df2))})
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


@app.task(bind=True)
def process_description(self,df):
    """parse vacancies description task"""
    print('Task:parsing_descriptions ',df)
    df2=pd.read_json(StringIO(df))
    self.update_state(state='PROGRESS', meta={'done': 0})
    for i,row in df2.iterrows():
        print(i,row)
        res = requests.post('http://description_analyzer:8000/parse_descriptions',
                        json={
                          "desc": row.vac_descr,
                        }, timeout=100)
        d = res.json()
        df = pd.DataFrame(json.loads(d))
        df['vac_id'] = row.vac_id
        df['site'] = row.site
        df.to_sql('vacancy_skills', con=CON, if_exists='append', index=False)
        self.update_state(state='PROGRESS', meta={'done': int(100.0*i/df2.shape[0])})

    return 'DONE'
