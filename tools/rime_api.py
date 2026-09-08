"""Small ctypes adapter for the public librime C API (BSD-licensed Rime API).

Structures follow rime_api.h, copyright RIME Developers. Adapter code GPL-3.0-only.
Only the stable prefix through candidate_list_end is used.
"""
import ctypes as C
import os
from pathlib import Path


class Traits(C.Structure):
    _fields_ = [("data_size", C.c_int)] + [(n, C.c_char_p) for n in (
        "shared_data_dir", "user_data_dir", "distribution_name", "distribution_code_name",
        "distribution_version", "app_name")] + [
        ("modules", C.POINTER(C.c_char_p)), ("min_log_level", C.c_int),
        ("log_dir", C.c_char_p), ("prebuilt_data_dir", C.c_char_p), ("staging_dir", C.c_char_p)]


class Composition(C.Structure):
    _fields_ = [(n, C.c_int) for n in ("length", "cursor_pos", "sel_start", "sel_end")] + [("preedit", C.c_char_p)]


class Candidate(C.Structure):
    _fields_ = [("text", C.c_char_p), ("comment", C.c_char_p), ("reserved", C.c_void_p)]


class Menu(C.Structure):
    _fields_ = [(n, C.c_int) for n in ("page_size", "page_no", "is_last_page", "highlighted_candidate_index", "num_candidates")] + [
        ("candidates", C.POINTER(Candidate)), ("select_keys", C.c_char_p)]


class Context(C.Structure):
    _fields_ = [("data_size", C.c_int), ("composition", Composition), ("menu", Menu),
                ("commit_text_preview", C.c_char_p), ("select_labels", C.POINTER(C.c_char_p))]


class Commit(C.Structure):
    _fields_ = [("data_size", C.c_int), ("text", C.c_char_p)]


class Iterator(C.Structure):
    _fields_ = [("ptr", C.c_void_p), ("index", C.c_int), ("candidate", Candidate)]


API_NAMES = """setup set_notification_handler initialize finalize start_maintenance is_maintenance_mode
join_maintenance_thread deployer_initialize prebuild deploy deploy_schema deploy_config_file sync_user_data
create_session find_session destroy_session cleanup_stale_sessions cleanup_all_sessions process_key
commit_composition clear_composition get_commit free_commit get_context free_context get_status free_status
set_option get_option set_property get_property get_schema_list free_schema_list get_current_schema select_schema
schema_open config_open config_close config_get_bool config_get_int config_get_double config_get_string
config_get_cstring config_update_signature config_begin_map config_next config_end simulate_key_sequence
register_module find_module run_task get_shared_data_dir get_user_data_dir get_sync_dir get_user_id
get_user_data_sync_dir config_init config_load_string config_set_bool config_set_int config_set_double
config_set_string config_get_item config_set_item config_clear config_create_list config_create_map
config_list_size config_begin_list get_input get_caret_pos select_candidate get_version set_caret_pos
select_candidate_on_current_page candidate_list_begin candidate_list_next candidate_list_end""".split()


class Api(C.Structure):
    _fields_ = [("data_size", C.c_int)] + [(name, C.c_void_p) for name in API_NAMES]


def sized(cls):
    obj = cls()
    obj.data_size = C.sizeof(cls) - C.sizeof(C.c_int)
    return obj


class Rime:
    def __init__(self, library: Path, plugin: Path | None = None):
        self.library = C.CDLL(str(library.resolve()), mode=getattr(C, "RTLD_GLOBAL", 0))
        if plugin:
            self.plugin = C.CDLL(str(plugin.resolve()), mode=getattr(C, "RTLD_GLOBAL", 0))
        self.library.rime_get_api.restype = C.POINTER(Api)
        self.api = self.library.rime_get_api().contents
        self.functions = {}
        self.session = 0

    def bind(self, name, result, *args):
        if name not in self.functions:
            if getattr(Api, name).offset + C.sizeof(C.c_void_p) > self.api.data_size + C.sizeof(C.c_int):
                raise RuntimeError(f"Rime API lacks {name}")
            address = getattr(self.api, name)
            if not address:
                raise RuntimeError(f"Rime API has null {name}")
            self.functions[name] = C.CFUNCTYPE(result, *args)(address)
        return self.functions[name]

    def initialize(self, user: Path):
        self.traits = sized(Traits)
        self.traits.shared_data_dir = str(user).encode()
        self.traits.user_data_dir = str(user).encode()
        self.traits.distribution_name = b"Suibi test"
        self.traits.distribution_code_name = b"suibi"
        self.traits.distribution_version = b"0.1.0"
        self.traits.app_name = b"rime.suibi_test"
        self.traits.min_log_level = 1
        self.traits.log_dir = str(user / "logs").encode()
        (user / "logs").mkdir(exist_ok=True)
        self.modules = (C.c_char_p * 4)(b"default", b"deployer", b"lua", None)
        self.traits.modules = self.modules
        self.bind("setup", None, C.POINTER(Traits))(C.byref(self.traits))
        self.bind("initialize", None, C.POINTER(Traits))(C.byref(self.traits))
        self.bind("deployer_initialize", None, C.POINTER(Traits))(C.byref(self.traits))
        if not self.bind("find_module", C.c_void_p, C.c_char_p)(b"lua"):
            raise RuntimeError("librime-lua is missing")

    def deploy(self, schema: Path):
        if not self.bind("deploy_schema", C.c_int, C.c_char_p)(str(schema).encode()):
            raise RuntimeError(f"Failed to deploy {schema}")

    def select(self, schema: str):
        if self.session:
            self.bind("destroy_session", C.c_int, C.c_size_t)(self.session)
        self.session = self.bind("create_session", C.c_size_t)()
        if not self.session or not self.bind("select_schema", C.c_int, C.c_size_t, C.c_char_p)(self.session, schema.encode()):
            raise RuntimeError(f"Cannot select {schema}")
        self.set_option("ascii_mode", False)

    def set_option(self, name, value):
        self.bind("set_option", None, C.c_size_t, C.c_char_p, C.c_int)(self.session, name.encode(), int(value))

    def key(self, code, mask=0):
        return bool(self.bind("process_key", C.c_int, C.c_size_t, C.c_int, C.c_int)(self.session, code, mask))

    def type(self, text):
        for char in text:
            self.key(ord(char))

    def clear(self):
        self.bind("clear_composition", None, C.c_size_t)(self.session)
        self.commit()

    def input(self):
        return (self.bind("get_input", C.c_char_p, C.c_size_t)(self.session) or b"").decode()

    def preedit(self):
        obj = sized(Context)
        if not self.bind("get_context", C.c_int, C.c_size_t, C.POINTER(Context))(self.session, C.byref(obj)):
            return ""
        try:
            return (obj.composition.preedit or b"").decode()
        finally:
            self.bind("free_context", C.c_int, C.POINTER(Context))(C.byref(obj))

    def candidates(self, limit=10000):
        iterator = Iterator()
        result = []
        if not self.bind("candidate_list_begin", C.c_int, C.c_size_t, C.POINTER(Iterator))(self.session, C.byref(iterator)):
            return result
        try:
            while self.bind("candidate_list_next", C.c_int, C.POINTER(Iterator))(C.byref(iterator)):
                result.append(((iterator.candidate.text or b"").decode(), (iterator.candidate.comment or b"").decode()))
                if len(result) >= limit:
                    break
        finally:
            self.bind("candidate_list_end", None, C.POINTER(Iterator))(C.byref(iterator))
        return result

    def commit(self):
        obj = sized(Commit)
        if not self.bind("get_commit", C.c_int, C.c_size_t, C.POINTER(Commit))(self.session, C.byref(obj)):
            return ""
        text = (obj.text or b"").decode()
        self.bind("free_commit", C.c_int, C.POINTER(Commit))(C.byref(obj))
        return text

    def version(self):
        return self.bind("get_version", C.c_char_p)().decode()

    def close(self):
        if self.session:
            self.bind("destroy_session", C.c_int, C.c_size_t)(self.session)
        self.bind("finalize", None)()
