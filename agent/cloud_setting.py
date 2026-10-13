from storage import load_json, save_json
from config import ALLOW_CLOUD_DEFAULT

CLOUD_SETTING_FILE = "cloud_setting.json"


def is_cloud_allowed():
    # Read fresh on every call, not a load-once constant like the old
    # config.ALLOW_CLOUD was — so a toggle (from the GUI or anywhere else)
    # takes effect on the very next message, no process restart needed.
    # Goes through storage.py like every other piece of persisted state,
    # so it gets the same encryption-at-rest treatment for free.
    setting = load_json(CLOUD_SETTING_FILE, None)

    if setting is not None and "allow_cloud" in setting:
        return setting["allow_cloud"]

    return ALLOW_CLOUD_DEFAULT


def set_cloud_allowed(value):
    save_json(CLOUD_SETTING_FILE, {"allow_cloud": bool(value)})
