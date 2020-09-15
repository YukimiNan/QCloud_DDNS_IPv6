import base64
import functools
import hashlib
import hmac
import json
import os
import random
import socket
import subprocess
import time

import requests

from fs import dump_json, load_json
from log import setLogger

MAIN_DIR = os.path.abspath(os.path.dirname(__file__))
LAST_IP_PATH = os.path.join(MAIN_DIR, 'last_ip.json')

logger = setLogger(dir_=os.path.join(MAIN_DIR, 'log'))


def get_host_ipv6():
    with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
        # Any most accessible IPv6 address. This default is aliyun's DNS server.
        # CHANGEME to an international accessible IP such as Google, if you're outside China.
        s.connect(('2400:3200::1', 53))
        return s.getsockname()[0]


def load_last_ip():
    return load_json(LAST_IP_PATH)


def save_last_ip(value):
    dump_json(value, LAST_IP_PATH)


def sign(req_method, req_host, req_path, req_params):
    SECRETID = 'Your own secret ID given by QCloud'  # CHANGEME
    SECRETKEY = 'Your own secret key given by QCloud'  # CHANGEME

    req_params = req_params.copy()

    timestamp = int(time.time())
    req_params.update({
        'Timestamp': timestamp,
        'Nonce': random.randint(1, timestamp),
        'SecretId': SECRETID,
        'SignatureMethod': 'HmacSHA256',
    })

    plain = sorted(req_params.items())
    plain = '&'.join(map(lambda i: f'{i[0]}={i[1]}', plain))
    plain = f'{req_method}{req_host}{req_path}?{plain}'
    plain = plain.encode('utf-8')

    hmac_ = hmac.HMAC(SECRETKEY.encode('utf-8'),
                      msg=plain,
                      digestmod=hashlib.sha256)
    req_params['Signature'] = base64.b64encode(hmac_.digest())

    return req_params


def sign_and_send(req_params, req_host):
    '''本函数应保证API调用成功，否则抛出异常
This function should ensure API call succeeded, else raise exception'''

    REQ_PROTOCOL = 'https'
    REQ_PATH = '/v2/index.php'
    REQ_METHOD = 'POST'

    signed = sign(REQ_METHOD, req_host, REQ_PATH, req_params)
    url = f'{REQ_PROTOCOL}://{req_host}{REQ_PATH}'

    res = requests.request(REQ_METHOD, url, data=signed)
    body = json.loads(res.text)

    if body['code'] != 0:
        logger.exception(body)
        raise Exception(body)

    return body


def list_filter_record():
    # Example: for update of "ipv6.lab.yukimi.cn", "domain" =  yukimi.cn", "subDomain" = "ipv6.lab"
    body = sign_and_send(
        {
            'Action': 'RecordList',
            'domain': 'Your own domain name hosted on QCloud',  # CHANGEME
            'offset': 0,
            'length': 20,
            'subDomain': 'Your own subdomain name, recorded under the above domain',  # CHANGEME
        }, 'cns.api.qcloud.com')  # CHANGEME to international API address if you can't access it

    return body['data']['records'][0]


def modify_record(id_, value):
    # Example: for update of "ipv6.lab.yukimi.cn", "domain" =  yukimi.cn", "subDomain" = "ipv6.lab"
    body = sign_and_send(
        {
            'Action': 'RecordModify',
            'domain': 'yukimi.cn',  # CHANGEME
            'recordId': id_,
            'subDomain': 'ipv6.lab',  # CHANGEME
            'recordType': 'AAAA',
            'recordLine': '默认',  # "默认" or "default"
            'value': value,
            'ttl': 600,
        }, 'cns.api.qcloud.com')  # CHANGEME to international API address if you can't access it

    return body


def restart_ssr():
    '''（Linux）重启SSR需要root权限
some restarting tasks(on Linux), after resolution record changed'''

    run = functools.partial(subprocess.run,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)

    proc = run('/etc/init.d/ssr stop')
    output = proc.stdout.decode()
    if proc.returncode != 0:
        logger.warning(output)
    else:
        logger.info(output)

    proc = run('/etc/init.d/ssr start')
    output = proc.stdout.decode()
    if proc.returncode != 0:
        logger.exception(output)
        raise Exception(output)
    else:
        logger.info(output)


def restart_wv2ray():
    '''（Windows）重启wv2ray需要管理员权限
some restarting tasks(on Windows), after resolution record changed'''

    run = functools.partial(subprocess.run,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)

    proc = run('TASKKILL /IM wv2ray.exe /F')
    output = proc.stdout.decode('gbk')
    if proc.returncode != 0:
        logger.warning(output)
    else:
        logger.info(output)

    retcode = os.system('start D:\\v2ray-windows-64\\wv2ray.exe')
    if retcode != 0:
        logger.exception('start wv2ray failed.')
        raise Exception()


def crontab_task():
    host_ipv6 = get_host_ipv6()
    last_ip = load_last_ip()

    if host_ipv6 != last_ip:
        record = list_filter_record()

        id_ = record['id']
        value = record['value']
        updated_on = record['updated_on']

        save_last_ip(value)

        if host_ipv6 != value:
            modify_record(id_, host_ipv6)
            save_last_ip(host_ipv6)
            logger.info("dns changed from %s(updated on %s) to %s", value,
                        updated_on, host_ipv6)

            # restart_ssr()
            # restart_wv2ray()


if __name__ == '__main__':
    try:
        crontab_task()
    except:
        logger.exception('')
