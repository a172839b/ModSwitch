import logging
import os

import orjson

log = logging.getLogger(__name__)


class JsonError(Exception):
    ...


def read(key, default: any = None, path: str = 'setting') -> any:
    try:
        data = read_json(path)[key]
    except KeyError:
        write(key, default, path)
        data = read_json(path)[key]
    return data


def write(key, value: any = None, path: str = 'setting'):
    json_data = read_json(path)
    json_bak = json_data.copy()
    try:
        json_data[key] = value
        write_json(path, json_data)
    except Exception as e:
        # 寫回正常資料
        log.error(f'write error: path: {path}, key: {key}, ex:{e}')
        write_json(path, json_bak)
        raise JsonError(f'{path}.json 寫入資料錯誤')


def read_json(name) -> dict:
    if not os.path.isfile(rf'{name}.json'):
        write_json(name, {})
    with open(rf'{name}.json', 'rb') as jsonFile:
        json_data = orjson.loads(jsonFile.read())
    return json_data


def write_json(name, json_data: dict):
    with open(rf'{name}.json', "wb") as file:
        file.write(orjson.dumps(json_data, option=orjson.OPT_INDENT_2))
