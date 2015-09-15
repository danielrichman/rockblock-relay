import os.path
import yaml

def setdefault(d, k, v):
    d.setdefault(k, v)
    if d[k] is None:
        d[k] = v

def load_config():
    base = os.path.join(os.path.dirname(__file__), "..")
    cfg_fn = os.path.join(base, "config.yaml")
    auth_fn = os.path.join(base, "auth.yaml")

    with open(cfg_fn) as f:
        cfg = yaml.safe_load(f)

    assert "email" in cfg
    setdefault(cfg, "imei", {})
    setdefault(cfg, "repeat", {})
    assert "imei_reverse" not in cfg

    imei_reverse = {}

    for name, imei in cfg["imei"].items():
        assert isinstance(imei, int)
        imei_reverse[imei] = name

    cfg["imei_reverse"] = imei_reverse

    imei = cfg["imei"]

    for key, targets in cfg["repeat"].items():
        assert key in imei
        for target in targets:
            assert target in imei

    try:
        with open(auth_fn) as f:
            auth = yaml.safe_load(f)

        for key in auth:
            assert key in imei

        cfg["auth"] = auth
        auth_error = None

    except Exception as e:
        auth_error = e

    return cfg, auth_error

config, auth_error = load_config()

def need_auth():
    if auth_error is not None:
        raise auth_error
