import json
from contextlib import contextmanager
from pathlib import Path
from typing import List, Tuple

from ruamel.yaml import YAML


def obj_retriever(obj: dict, key_path: str) -> Tuple[dict, str]:
    ob = obj
    path = key_path.split("/")
    while len(path) > 1:
        k = path.pop(0)
        try:
            ob = ob[k]
        except KeyError:
            ob[k] = None

    last_k = path[0]
    return ob, last_k


def load_config(kind):
    if kind == 'yaml':
        yaml = YAML(typ='safe')
        config_file = Path("../logger_tt/log_config.yaml")
        log_config = yaml.load(config_file.read_text())
        return log_config

    if kind == 'json':
        config_file = Path("../logger_tt/log_config.json")
        log_config = json.loads(config_file.read_text())
        return log_config

    raise ValueError(f'"kind" must be either "yaml" or "json", but got: {kind}')


def dump_config(out_name: str, config: dict) -> Path:
    test_config = Path(out_name)

    if out_name.endswith('yaml'):
        yaml = YAML(typ='safe')
        yaml.dump(data=config, stream=test_config)

    if out_name.endswith('json'):
        test_config.write_text(json.dumps(config, indent=4))

    return test_config


@contextmanager
def config_modified(out_name: str, key_val: List[tuple]) -> Path:
    # todo: move this func to a util file and compact other tests
    # read in default config
    log_config = load_config(out_name[-4:])

    # update config
    for key, val in key_val:
        ob, last_k = obj_retriever(log_config, key)

        if isinstance(val, str) and val.startswith('k:'):
            # use another item in the dict as value
            val_key_path = val[2:]
            val_ob, val_k = obj_retriever(log_config, val_key_path)
            ob[last_k] = val_ob[val_k]
        else:
            # normal object
            ob[last_k] = val

    # write the config out
    test_config = dump_config(out_name, log_config)

    # yield context
    try:
        yield test_config
    finally:
        # delete it
        test_config.unlink()
