import os.path
import yaml

def load_config():
    fn = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(fn) as f:
        # YAML seems to notice that the IMEIs are integers and casts them
        # to ints (even when they're dictionary keys!), which is what we want.
        # I assert that this is the case in case we later get keys as strings,
        # which will break dictionary lookups completely.

        cfg = yaml.safe_load(f)

        for key in {"auth", "repeat"}:
            for key2 in cfg.get(key, {}).keys():
                assert isinstance(key2, int)

        for value in cfg.get("repeat", {}).values():
            for item in value:
                assert isinstance(item, int)

        return cfg

config = load_config()
