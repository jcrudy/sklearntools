from sympy.functions.elementary.exponential import exp
from sympy.core.numbers import RealNumber
from .linear_regression import sym_predict_linear
from sklearn.linear_model.logistic import LogisticRegression
from ..sym_predict import register_sym_predict
from ..input_size import register_input_size, input_size_from_coef
from ..sym_predict_proba import register_sym_predict_proba


def sym_predict_logistic_regression(logistic_regression):
    return RealNumber(1) / (RealNumber(1) + exp(-sym_predict_linear(logistic_regression)))

register_sym_predict(LogisticRegression, sym_predict_logistic_regression)
register_input_size(LogisticRegression, input_size_from_coef)
register_sym_predict_proba(LogisticRegression, sym_predict_logistic_regression,)