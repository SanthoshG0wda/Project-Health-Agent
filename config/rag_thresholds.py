import os

import yaml


def load_thresholds(config_path=None):
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "rag_thresholds.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def save_thresholds(config_path, cfg):
    with open(config_path, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
