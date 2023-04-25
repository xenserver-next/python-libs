from _typeshed import Incomplete
from collections import OrderedDict as MaybeOrderedDict
from typing import NamedTuple

# MaybeOrderedDict = dict

class SkipTest(Exception): ...

PY3: Incomplete
PY2: Incomplete
PYTEST4: Incomplete

class InstanceType: ...

lzip: Incomplete
text_type = str
string_types: Incomplete
bytes_type = bytes

def make_method(func, instance, type): ...
def to_text(x): ...

class CompatArgSpec(NamedTuple):
    args: Incomplete
    varargs: Incomplete
    keywords: Incomplete
    defaults: Incomplete

def getargspec(func): ...
def skip_on_empty_helper(*a, **kw) -> None: ...
def reapply_patches_if_need(func): ...
def delete_patches_if_need(func) -> None: ...

class _param(NamedTuple):
    args: Incomplete
    kwargs: Incomplete

class param(_param):
    def __new__(cls, *args, **kwargs): ...
    @classmethod
    def explicit(cls, args: Incomplete | None = ..., kwargs: Incomplete | None = ...): ...
    @classmethod
    def from_decorator(cls, args): ...

class QuietOrderedDict(MaybeOrderedDict): ...  # type: ignore

def parameterized_argument_value_pairs(func, p): ...
def short_repr(x, n: int = ...): ...
def default_doc_func(func, num, p): ...
def default_name_func(func, num, p): ...
def set_test_runner(name) -> None: ...
def detect_runner(): ...

class parameterized:
    get_input: Incomplete
    doc_func: Incomplete
    skip_on_empty: Incomplete
    def __init__(self, input, doc_func: Incomplete | None = ..., skip_on_empty: bool = ...) -> None: ...
    def __call__(self, test_func): ...
    def param_as_nose_tuple(self, test_self, func, num, p): ...
    def assert_not_in_testcase_subclass(self) -> None: ...
    @classmethod
    def input_as_callable(cls, input): ...
    @classmethod
    def check_input_values(cls, input_values): ...
    @classmethod
    def expand(cls, input, name_func: Incomplete | None = ..., doc_func: Incomplete | None = ..., skip_on_empty: bool = ..., **legacy): ...
    @classmethod
    def param_as_standalone_func(cls, p, func, name): ...
    @classmethod
    def to_safe_name(cls, s): ...

def parameterized_class(attrs, input_values: Incomplete | None = ..., class_name_func: Incomplete | None = ..., classname_func: Incomplete | None = ...): ...
def unwrap_mock_patch_func(f): ...
def get_class_name_suffix(params_dict): ...
def default_class_name_func(cls, num, params_dict): ...
