#!/usr/bin/env python3

import requests

def test_hh_grabber():
    res = requests.get('http://localhost:8002/health')
    print(res)
    print(res.json())
    assert res.json() == 'ok'