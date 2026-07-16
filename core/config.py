from json import dump, load
from os import makedirs


DATA_DIR = "data"
REGION_FILE = f"{DATA_DIR}/region.json"
EMOJI_FILE = f"{DATA_DIR}/emoji.json"

# ── LLM 共用參數 ──
LLM_MODEL = "gemini-2.5-flash"
LLM_TEMPERATURE = 0.5
LLM_MAX_OUTPUT_TOKENS = 900


class _AutoSaveDict(dict):
    def __init__(self, *args, save_func=None, **kwargs):
        self._save_func = save_func
        self._initialized = False
        super().__init__(*args, **kwargs)
        self._initialized = True

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self._initialized and self._save_func:
            self._save_func(self)

    def __delitem__(self, key):
        super().__delitem__(key)
        if self._initialized and self._save_func:
            self._save_func(self)


class RuntimeConfig:
    def __init__(self):
        makedirs(DATA_DIR, exist_ok=True)
        self._region = self._load_region()
        self._emoji: _AutoSaveDict = self._load_emoji()

    # ── region ──
    def _load_region(self) -> str:
        try:
            with open(REGION_FILE) as f:
                return load(f).get("last_region", "india")
        except (FileNotFoundError, ValueError):
            return "india"

    def _save_region(self) -> None:
        with open(REGION_FILE, "w") as f:
            dump({"last_region": self._region}, f)

    @property
    def last_region(self) -> str:
        return self._region

    @last_region.setter
    def last_region(self, value: str):
        self._region = value
        self._save_region()

    # ── emoji ──
    def _load_emoji(self) -> _AutoSaveDict:
        def _save(d: _AutoSaveDict):
            with open(EMOJI_FILE, "w", encoding="utf-8") as f:
                dump(dict(d), f, ensure_ascii=False, indent=4)

        try:
            with open(EMOJI_FILE, encoding="utf-8") as f:
                return _AutoSaveDict(load(f), save_func=_save)
        except (FileNotFoundError, ValueError):
            return _AutoSaveDict(save_func=_save)

    @property
    def emoji_settings(self) -> _AutoSaveDict:
        return self._emoji


runtime: RuntimeConfig = RuntimeConfig()
