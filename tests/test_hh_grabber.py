#!/usr/bin/env python3

import requests
import dotenv
from os import getenv

def test_hh_grabber_health():
    res = requests.get('http://localhost:8001/health')
    print(res)
    print(res.json())
    assert res.json() == 'ok'

def test_hh_grabber():
    dotenv.load_dotenv(dotenv.find_dotenv())
    login = getenv('HH_LOGIN')
    password = getenv('HH_PASSWORD')
    res = requests.post('http://localhost:8001/find_vacancies',
                        json={
                          "phone": login,
                          "password": password,
                          "request": 'Senior data-science team lead'
                        })
    assert res.status_code == 200
    d=res.json()
    df = pd.DataFrame(json.loads(d))
    assert len(df) > 10
