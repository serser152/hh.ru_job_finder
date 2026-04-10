#!/usr/bin/env python3
"""
tests for grabber api
"""

import json
from os import getenv
import requests
import dotenv
import pandas as pd

def test_grabber_health():
    """Test grabber health"""
    res = requests.get('http://localhost:8001/health', timeout=60)
    print(res)
    print(res.json())
    assert res.json() == 'ok'


def test_hh_grabber():
    """Test hh grabber"""

    dotenv.load_dotenv(dotenv.find_dotenv())
    login = getenv('HH_LOGIN')
    password = getenv('HH_PASSWORD')
    res = requests.post('http://localhost:8001/find_vacancies',
                        json={
                          "site": "hh.ru",
                          "phone": login,
                          "password": password,
                          "request": 'Senior data-science team lead'
                        }, timeout=60)
    assert res.status_code == 200
    d=res.json()
    df = pd.DataFrame(json.loads(d))
    assert len(df) > 10

def test_zp_grabber():
    """Test zp grabber"""

    dotenv.load_dotenv(dotenv.find_dotenv())
    login = getenv('ZARPLATA_LOGIN')
    password = getenv('ZARPLATA_PASSWORD')
    res = requests.post('http://localhost:8001/find_vacancies',
                        json={
                          "site": "zarplata.ru",
                          "phone": login,
                          "password": password,
                          "request": 'Senior data-science team lead'
                        }, timeout=60)
    assert res.status_code == 200
    d=res.json()
    df = pd.DataFrame(json.loads(d))
    assert len(df) > 10
