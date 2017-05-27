from sympy.core.symbol import Symbol
from .input_size import input_size
from .base import call_method_or_dispatch, create_registerer
from sklearn.base import BaseEstimator

def syms_x(estimator):
    return [Symbol('x%d' % d) for d in range(input_size(estimator))]

syms_dispatcher = {
                   BaseEstimator: syms_x,
                   }
syms = call_method_or_dispatch('syms', syms_dispatcher)
register_syms = create_registerer(syms_dispatcher, 'register_syms')