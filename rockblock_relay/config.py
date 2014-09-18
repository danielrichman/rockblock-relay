import os.path
import yaml

def load_config():
    fn = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(fn) as f:
        cfg = yaml.safe_load(f)
        cfg.setdefault("imei", {})
        cfg.setdefault("auth", {})
        cfg.setdefault("repeat", {})
        assert "imei_reverse" not in cfg

        imei_reverse = {}

        for name, imei in cfg["imei"].items():
            assert isinstance(imei, int)
            imei_reverse[imei] = name

        cfg["imei_reverse"] = imei_reverse

        imei = cfg["imei"]

        for key in {"auth", "repeat"}:
            for key2 in cfg[key]:
                assert key2 in imei

        for targets in cfg["repeat"].values():
            for target in targets:
                assert target in imei

        return cfg

config = load_config()
