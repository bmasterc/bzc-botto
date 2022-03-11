
import requests, json as json_, os, pytz, time, hashlib, re
from datetime import datetime, timedelta
from copy import deepcopy
from bson import json_util

def cleanFileName(file_name):
    return "".join(x for x in file_name if x.isalnum())

def from_unix(ticks, timezone='UTC', ignore_tz=False) -> datetime:
    tm = datetime.utcfromtimestamp(ticks)
    if ignore_tz: return tm

def getUTCNow(days=None) -> datetime:
    if days:
        return datetime.now(pytz.utc) + timedelta(days=days)
    return datetime.now(pytz.utc)

def mkdir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def writeFile(path, content, append=False):
    with open(path, 'a' if append else 'w', encoding="utf-8") as file:
        file.truncate()
        if isinstance(content, tuple) or isinstance(content, list):
            for line in content:
                file.write(str(line) + '\n')
        else:
            file.write(content)

def writeJsonFile(path, jsonContent, pretty=False, append=False):
    with open(path, 'a' if append else 'w') as file:
        if not append: file.truncate()
        # file.write(json_.dumps(jsonContent, default=date_handler, sort_keys=True, indent=4))
        if pretty:
            file.write(json_.dumps(jsonContent, default=json_util.default, sort_keys=True, indent=4))
        else:
            file.write(json_.dumps(jsonContent, default=json_util.default))

def appendFile(path, content):
    writeFile(path, content, append=True)

def readFile(path):
    with open(path, 'r', encoding="utf-8") as file:
        return file.read()

def jloads(json_str):
    return json_.load(json_str, object_hook=json_util.object_hook)

def readJsonFile(path):
    with open(path, 'r') as file:
        return jloads(file)

def md5(msg):
    return hashlib.md5(msg.encode('utf-8')).hexdigest()

def reg(text, pattern, index=None, options=re.IGNORECASE | re.DOTALL, all=False, return_location=False):
    if all:
        ret = []
        for mat in re.finditer(pattern, text, options):
            m = _reg(mat, index, return_location)
            if m:
                ret.append(m)
        if len(ret):
            return ret
    else:
        return _reg(re.search(pattern, text, options), index, return_location)
def _reg(mat, index, return_location):
    if mat:
        grp = mat.groups()
        if not isinstance(index, int):
            if grp:
                if type(grp) is tuple and len(grp) == 1:
                    grp = grp[0]
                ret =  grp
            else:
                ret =  True
        else:
            if index == 0:
                ret =  mat.group(0)
            elif len(grp) > index-1:
                ret =  grp[index-1]
            else:
                ret = False
    else:
        ret = False

    if return_location and mat.regs:
        ret = (ret, mat.regs)

    return ret

class WebSession(requests.Session):
    TempDir = 'data/temp/'

    def __init__(self):
        requests.Session.__init__(self)

        self.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
                                     '(KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36'

    def set_auth(self, username, password):
        self.auth = (username, password)

    def get_url_retry(self, *args, raise_error=True, max_retries=4, retry_delay=0.5, **kwargs):
        errors = 0
        last_error = None
        while errors < max_retries:
            try:
                ret = self.get_url(*args, raise_error=raise_error, **kwargs)
                return ret
            except Exception as e:
                errors += 1
                last_error = e
                time.sleep(retry_delay)

        if last_error and raise_error:
            raise last_error

    def get_url(self, url, post=False, data=None, headers=None, return_response=False, cache_expire=None,
                verify=True, raise_error=True, timeout=10, json=None, delete=False, put=False, patch=False, params=None, invalidate_cache=False):
        cache_file = None
        if cache_expire:
            ftn_params = deepcopy(locals())
            del ftn_params['self']
            del ftn_params['cache_expire']
            del ftn_params['headers']
            del ftn_params['cache_file']
            del ftn_params['invalidate_cache']
            cache_file = f'{WebSession.TempDir}{cleanFileName(url)[-200:]}_{md5(json_.dumps(ftn_params))}.cache'

            if os.path.exists(cache_file):
                if not invalidate_cache and (cache_expire == -1 or from_unix(os.path.getmtime(cache_file)) > getUTCNow() - cache_expire):
                    text = readFile(cache_file)
                    js = None
                    if text[0] in ('[', '{'):
                        try: js = json_.loads(text)
                        except: pass
                    if return_response:
                        class Container(object):
                            def json(self):
                                return self.js
                        ret = Container()
                        ret.is_json = True
                        ret.from_cache = True
                        ret.text = text
                        ret.status_code = 200
                        ret.js = js
                        return ret
                    return js if js is not None else text
                else:
                    os.remove(cache_file)
                    if invalidate_cache:
                        return

        if data and isinstance(data, (dict, list)):
            data = json_.dumps(data)
            if headers:
                headers["Content-Type"] = 'application/json'
            else:
                headers = {"Content-Type": 'application/json'}

        if delete:
            r = self.delete(url, json=json, data=data, params=params,
                         verify=verify, headers=headers, timeout=timeout, allow_redirects=True)
        elif put:
            r = self.put(url, json=json, data=data, params=params,
                          verify=verify, headers=headers, timeout=timeout, allow_redirects=True)
        elif patch:
            r = self.patch(url, json=json, data=data, params=params,
                          verify=verify, headers=headers, timeout=timeout, allow_redirects=True)
        elif post or data:
            r = self.post(url, json=json, data=data, params=params,
                          verify=verify, headers=headers, timeout=timeout, allow_redirects=True)
        else:
            r = self.get(url, params=params, verify=verify, headers=headers, timeout=timeout, allow_redirects=True)

        if raise_error:
            r.raise_for_status()

        r.is_json = 'Content-Type' in r.headers and 'application/json' in r.headers['Content-Type']

        if cache_file and r.status_code >= 200 and r.status_code < 400:
            mkdir(WebSession.TempDir)
            writeFile(cache_file, r.text)

        if return_response:
            r.from_cache = False
            return r

        if r.is_json:
            try:
                return r.json()
            except: pass

        js = None
        if r.text and r.text[0] in ('[', '{'):
            try:
                js = json_.loads(r.text)
                return js
            except:
                pass

        return r.text
