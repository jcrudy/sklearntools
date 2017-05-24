from .syms import syms
from .sym_predict import sym_predict
from .base import fallback, call_method_or_dispatch
from .parts import double_check

def sym_predict_parts_base(obj, target=None):
    return (syms(obj), [sym_predict(obj)], target)

sym_predict_parts_dispatcher = {}
sym_predict_parts = double_check(fallback(call_method_or_dispatch('sym_predict_parts', sym_predict_parts_dispatcher), sym_predict_parts_base))

