'''
Created on Feb 23, 2016

@author: jason
'''
import numpy as np
from sklearntools.sklearntools import StagedEstimator, MaskedEstimator,\
    ColumnSubsetTransformer, NonNullSubsetFitter, safe_assign_column
from sklearn.linear_model.base import LinearRegression
from sklearn.linear_model.logistic import LogisticRegression
from sklearntools.calibration import CalibratedEstimatorCV, ResponseTransformingEstimator,\
    LogTransformer, PredictorTransformer, HazardToRiskEstimator,\
    MovingAverageSmoothingEstimator, ThresholdClassifier, ProbaPredictingEstimator

from sklearntools.feature_selection import SingleEliminationFeatureImportanceEstimatorCV,\
    BackwardEliminationEstimator, UnivariateFeatureImportanceEstimatorCV,\
    BestKFeatureSelector
from numpy.testing.utils import assert_raises
from sklearntools.glm import GLM
import statsmodels.api as sm
import warnings
import pandas
from sklearntools.model_selection import ModelSelector
from sklearntools.scoring import log_loss_metric
from sklearn.ensemble.forest import RandomForestRegressor
from numpy.ma.testutils import assert_array_almost_equal
from sklearntools.earth import Earth
from sklearntools.kfold import CrossValidatingEstimator
from sklearn.metrics.regression import r2_score
from sklearn.model_selection import KFold
from nose.tools import assert_list_equal
warnings.simplefilter("error")

def test_safe_assign_column():
    data = pandas.DataFrame({'A': [1,2,3], 'B': [4,5,6]})
    safe_assign_column(data, 'A', [7,8,9])
    assert_list_equal(list(sorted(data.columns)), ['A', 'B'])

def test_single_elimination_feature_importance_estimator_cv():
    np.random.seed(0)
    m = 100000
    n = 6
    factor = .9
    
    X = np.random.normal(size=(m,n))
    beta = 100 * np.ones(shape=n)
    for i in range(1, n):
        beta[i] = factor * beta[i-1]
    beta = np.random.permutation(beta)[:,None]
    
    y = np.dot(X, beta) + 0.01 * np.random.normal(size=(m, 1))
    
    target_sequence = np.ravel(np.argsort(beta ** 2, axis=0))
    model1 = SingleEliminationFeatureImportanceEstimatorCV(LinearRegression())
    model1.fit(X, y)
    fitted_sequence = np.ravel(np.argsort(model1.feature_importances_, axis=0))
    
    np.testing.assert_array_equal(fitted_sequence, target_sequence)

def test_univariate_feature_importance_estimator_cv():
    np.random.seed(0)
    m = 100000
    n = 6
    factor = .9
    
    X = np.random.normal(size=(m,n))
    beta = 100 * np.ones(shape=n)
    for i in range(1, n):
        beta[i] = factor * beta[i-1]
    beta = np.random.permutation(beta)[:,None]
    
    y = np.dot(X, beta) + 0.01 * np.random.normal(size=(m, 1))
    
    target_sequence = np.ravel(np.argsort(beta ** 2, axis=0))
    model1 = UnivariateFeatureImportanceEstimatorCV(LinearRegression())
    model1.fit(X, y)
    fitted_sequence = np.ravel(np.argsort(model1.feature_importances_, axis=0))
    
    np.testing.assert_array_equal(fitted_sequence, target_sequence)

def test_k_best_feature_selector():
    np.random.seed(0)
    m = 100000
    n = 6
    factor = .9
    
    X = np.random.normal(size=(m,n))
    beta = 100 * np.ones(shape=n)
    for i in range(1, n):
        beta[i] = factor * beta[i-1]
    beta = np.random.permutation(beta)[:,None]
#     beta = np.random.normal(size=(n,1))
    
    y = np.dot(X, beta) + 0.01 * np.random.normal(size=(m, 1))
    
    target_vars = np.ravel(np.argsort(beta ** 2, axis=0))[::-1][:3]
    target_support = np.zeros(shape=n, dtype=bool)
    target_support[target_vars] = True
    
    model1 = BestKFeatureSelector(UnivariateFeatureImportanceEstimatorCV(LinearRegression()), k=3)
    model1.fit(X, y)
    
    np.testing.assert_array_equal(model1.support_, target_support)
    
def test_backward_elimination_estimation():
    np.random.seed(0)
    m = 100000
    n = 6
    factor = .9
    
    X = np.random.normal(size=(m,n))
    beta = 100 * np.ones(shape=n)
    for i in range(1, n):
        beta[i] = factor * beta[i-1]
    beta = np.random.permutation(beta)[:,None]
#     beta = np.random.normal(size=(n,1))
    
    y = np.dot(X, beta) + 0.01 * np.random.normal(size=(m, 1))
    
    target_sequence = np.ravel(np.argsort(beta ** 2, axis=0))
    model1 = BackwardEliminationEstimator(SingleEliminationFeatureImportanceEstimatorCV(LinearRegression()))
    model1.fit(X, y)
    
#     model2 = BRFE(FeatureImportanceEstimatorCV(LinearRegression()))
#     model2.fit(X, y)
    
    np.testing.assert_array_equal(model1.elimination_sequence_, target_sequence)

def test_multiple_response_regressor():
    np.random.seed(1)
    m = 100000
    n = 10
    
    X = np.random.normal(size=(m,n))
    beta1 = np.random.normal(size=(n,1))
    beta2 = np.random.normal(size=(n,1))
     
    y1 = np.dot(X, beta1)
    p2 = 1. / (1. + np.exp( - np.dot(X, beta2)))
    y2 = np.random.binomial(n=1, p=p2)
    y = np.concatenate([y1, y2], axis=1)
        
    model = MaskedEstimator(LinearRegression(), [True, False]) & MaskedEstimator(ProbaPredictingEstimator(LogisticRegression()), [False, True])
#     MultipleResponseEstimator([('linear', np.array([True, False], dtype=bool), LinearRegression()), 
#                                        ('logistic', np.array([False, True], dtype=bool), ProbaPredictingEstimator(LogisticRegression()))])
    model.fit(X, y)
    
    assert np.mean(beta1 - model.estimators_[0].estimator_.coef_) < .01
    assert np.mean(beta2 - model.estimators_[1].estimator_.estimator_.coef_) < .01
    model.get_params()
    model.predict(X)

def test_calibration():
    np.random.seed(1)
    m = 10000
    n = 10
    
    X = np.random.normal(size=(m,n))
    beta = np.random.normal(size=(n,1))
    y_lin = np.dot(X, beta)
    y_clas = np.random.binomial( 1, 1. / (1. + np.exp(-y_lin)) )
    y = np.concatenate([y_lin, y_clas], axis=1)
    estimator = MaskedEstimator(LinearRegression(), np.array([True, False], dtype=bool))
    calibrator = MaskedEstimator(LogisticRegression(), [False, True])
#     estimator = linear_regressor & calibrator
#     MultipleResponseEstimator([('estimator', np.array([True, False], dtype=bool), LinearRegression())])
#     calibrator = MultipleResponseEstimator([('calibrator', np.array([False, True], dtype=bool), LogisticRegression())])
    model = CalibratedEstimatorCV(estimator, calibrator, cv=KFold(n_splits=4, shuffle=True), n_jobs=1)
    model.fit(X, y)
    assert np.max(beta[:, 0] - model.estimator_.estimator_.coef_) < .000001
    assert np.max(model.calibrator_.estimator_.coef_ - 1.) < .1

def test_predictor_transformer_calibration():
    np.random.seed(1)
    m = 10000
    n = 10
    
    X = np.random.normal(size=(m,n))
    beta = np.random.normal(size=(n,1))
    y_lin = np.dot(X, beta)
    y_clas = np.random.binomial( 1, 1. / (1. + np.exp(-y_lin)) )
    y = np.concatenate([y_lin, y_clas], axis=1)
    estimator = MaskedEstimator(LinearRegression(), np.array([True, False], dtype=bool))
    calibrator = MaskedEstimator(LogisticRegression(), [False, True])
#     estimator = linear_regressor & calibrator
#     MultipleResponseEstimator([('estimator', np.array([True, False], dtype=bool), LinearRegression())])
#     calibrator = MultipleResponseEstimator([('calibrator', np.array([False, True], dtype=bool), LogisticRegression())])
    model = PredictorTransformer(estimator) >> calibrator
    model.fit(X, y)
    assert np.max(beta[:, 0] - model.intermediate_stages_[0].estimator_.estimator_.coef_) < .000001
    assert np.max(model.final_stage_.estimator_.coef_ - 1.) < .1
    
def test_pipeline():
    np.random.seed(1)
    m = 10000
    n = 10
    
    X = np.random.normal(size=(m,n))
    beta = np.random.normal(size=(n,1))
    beta[np.random.binomial(p=2.0/float(n), n=1, size=n).astype(bool)] = 0
    y = np.dot(X, beta) + 0.5 * np.random.normal(size=(m, 1))
    beta_reduced = beta[beta != 0]
    
    model = BackwardEliminationEstimator(SingleEliminationFeatureImportanceEstimatorCV(LinearRegression())) 
    model >>= LinearRegression()
    
    model.fit(X, y)
    assert np.max(np.abs(model.final_stage_.coef_ - beta_reduced)) < .1

def test_response_transforming_estimator():
    np.random.seed(1)
    m = 10000
    n = 10
    
    X = np.random.normal(size=(m,n))
    beta = np.random.normal(size=(n,1))
    sigma = .1
    y_pre = np.dot(X, beta) + sigma * np.random.normal(size=(m,1))
    y_post = np.exp(y_pre)
    
    model = ResponseTransformingEstimator(LinearRegression(), LogTransformer(offset=0.))
    model.fit(X, y_post)
    
    assert np.abs(np.mean(model.predict(X) - y_pre)) < .01
    
    # Because LinearRegression has no transform method
    assert_raises(AttributeError, lambda: model.transform(X))
    
def test_hazard_to_risk():
    np.random.seed(1)
    
    m = 10000
    n = 10
    
    # Simulate an event under constant hazard, with hazard = X * beta and 
    # iid exponentially distributed exposure times.
    X = np.random.normal(size=(m,n))
    beta = np.random.normal(size=(n,1))
    hazard = np.exp(np.dot(X, beta))
    exposure = np.random.exponential(size=(m,1))
    rate = np.random.poisson(hazard * exposure) / exposure
    
    model = CalibratedEstimatorCV(GLM(sm.families.Gaussian(sm.families.links.log), add_constant=False), 
                                  ProbaPredictingEstimator(ThresholdClassifier(HazardToRiskEstimator(LogisticRegression()))))
    
    model.fit(X, rate, exposure=exposure)
    
    y_pred = model.predict(X, exposure)
    assert np.abs((np.sum(y_pred) - np.sum(rate > 0)) / np.sum(rate > 0))  < .1
    assert np.max(np.abs(model.estimator_.coef_ - beta[:,0])) < .1

def test_hazard_to_risk_staged():
    np.random.seed(1)
    
    m = 10000
    n = 10
    
    # Simulate an event under constant hazard, with hazard = X * beta and 
    # iid exponentially distributed exposure times.
    X = np.random.normal(size=(m,n))
    beta = np.random.normal(size=(n,1))
    hazard = np.exp(np.dot(X, beta))
    exposure = np.random.exponential(size=(m,1))
    rate = np.random.poisson(hazard * exposure) / exposure
    
    model = CalibratedEstimatorCV(GLM(sm.families.Gaussian(sm.families.links.log), add_constant=False), 
                                  ProbaPredictingEstimator(ThresholdClassifier(HazardToRiskEstimator(LogisticRegression()))))
    
    model.fit(X, rate, exposure=exposure)
    
    y_pred = model.predict(X, exposure)
    assert np.abs((np.sum(y_pred) - np.sum(rate > 0)) / np.sum(rate > 0))  < .1
    assert np.max(np.abs(model.estimator_.coef_ - beta[:,0])) < .1

def test_moving_average_smoothing_estimator():
    np.random.seed(1)
    
    m = 10000
    n = 10
    
    # Simulate an event under constant hazard, with hazard = X * beta and 
    # iid exponentially distributed exposure times.
    X = np.random.normal(size=(m,n))
    beta = np.random.normal(size=(n,1))
    hazard = np.exp(np.dot(X, beta))
    exposure = np.random.exponential(size=(m,1))
    rate = np.random.poisson(hazard * exposure) / exposure
    
    model = CalibratedEstimatorCV(GLM(sm.families.Gaussian(sm.families.links.log), add_constant=False), 
                                  ThresholdClassifier(HazardToRiskEstimator(MovingAverageSmoothingEstimator(RandomForestRegressor()))))
    
    model.fit(X, rate, exposure=exposure)
    
    y_pred = model.predict(X, exposure)
    assert np.abs((np.sum(y_pred) - np.sum(rate > 0)) / np.sum(rate > 0))  < .1
    assert np.max(np.abs(model.estimator_.coef_ - beta[:,0])) < .1

def test_staged_estimator():
    np.random.seed(1)
    m = 10000
    n = 10
    
    X = np.random.normal(size=(m,n))
    beta = np.random.normal(size=(n,1))
    beta[np.random.binomial(p=2.0/float(n), n=1, size=n).astype(bool)] = 0
    y = np.dot(X, beta) + 0.5 * np.random.normal(size=(m, 1))
    beta_reduced = beta[beta != 0]
    
    stage0 = BackwardEliminationEstimator(SingleEliminationFeatureImportanceEstimatorCV(LinearRegression())) 
    stage1 = LinearRegression()
    model = StagedEstimator([stage0, stage1])
    
    model.fit(X, y)
    assert np.max(np.abs(model.final_stage_.coef_ - beta_reduced)) < .1
#     
#     y_lin = np.dot(X, beta)
#     y_clas = np.random.binomial( 1, 1. / (1. + np.exp(-y_lin)) )
#     y = np.concatenate([y_lin, y_clas], axis=1)
#     estimator = mask_estimator(LinearRegression(), np.array([True, False], dtype=bool))
#     calibrator = mask_estimator(LogisticRegression(), [False, True])
# #     estimator = linear_regressor & calibrator
# #     MultipleResponseEstimator([('estimator', np.array([True, False], dtype=bool), LinearRegression())])
# #     calibrator = MultipleResponseEstimator([('calibrator', np.array([False, True], dtype=bool), LogisticRegression())])
#     model = CalibratedEstimatorCV(estimator, calibrator)
#     model.fit(X, y)
#     assert np.max(beta[:, 0] - model.estimator_.estimators_[0][2].coef_) < .000001
#     assert np.max(model.calibrator_.estimators_[0][2].coef_ - 1.) < .1

def test_column_subset_transformer():
    m = 1000
    n = 10
    X = np.random.normal(size=(m,n))
    x_cols = [0,3,4,5]
    y_cols = 9
    sample_weight_cols = 8
    exposure_cols = 7
    
    subsetter1 = ColumnSubsetTransformer(x_cols=x_cols, y_cols=y_cols, 
                                         sample_weight_cols=sample_weight_cols,
                                         exposure_cols=exposure_cols)
    np.testing.assert_array_equal(subsetter1.transform(X), X[:, x_cols])
    args = {'X': X}
    subsetter1.update(args)
    np.testing.assert_array_equal(args['X'], X[:, x_cols])
    np.testing.assert_array_equal(args['y'], X[:, y_cols])
    np.testing.assert_array_equal(args['sample_weight'], X[:, sample_weight_cols])
    np.testing.assert_array_equal(args['exposure'], X[:, exposure_cols])
    
    X_ = pandas.DataFrame(X, columns=['x%d' % n for n in range(10)])
    x_cols_ = ['x%d' % n for n in x_cols]
    y_cols_ = 'x%d' % y_cols
    sample_weight_cols_ = 'x%d' % sample_weight_cols
    exposure_cols_ = 'x%d' % exposure_cols
    subsetter2 = ColumnSubsetTransformer(x_cols=x_cols_, y_cols=y_cols_, 
                                         sample_weight_cols=sample_weight_cols_,
                                         exposure_cols=exposure_cols_)
    np.testing.assert_array_equal(subsetter2.transform(X_), X[:, x_cols])
    args_ = {'X': X_}
    subsetter2.update(args_)
    np.testing.assert_array_equal(args_['X'], X[:, x_cols])
    np.testing.assert_array_equal(args_['y'], X[:, y_cols])
    np.testing.assert_array_equal(args_['sample_weight'], X[:, sample_weight_cols])
    np.testing.assert_array_equal(args_['exposure'], X[:, exposure_cols])
    
    lin = ColumnSubsetTransformer(x_cols=x_cols_, y_cols=y_cols_) >> LinearRegression()
    lin.fit(X_)
    lin.predict(X_.loc[:, x_cols_])
    lin.score(X_)

def test_model_selector():
    np.random.seed(1)
    
    m = 10000
    n = 10
    
    # Simulate an event under constant hazard, with hazard = X * beta and 
    # iid exponentially distributed exposure times.
    X = np.random.normal(size=(m,n))
    beta = np.random.normal(size=(n,1))
    hazard = np.exp(np.dot(X, beta))
    exposure = np.random.exponential(size=(m,1))
    rate = np.random.poisson(hazard * exposure) / exposure
    best_subset = np.ravel(np.argsort(np.abs(beta))[::-1][:3])
    worst_subset = np.ravel(np.argsort(np.abs(beta))[:3])
    
    basic_model = CalibratedEstimatorCV(GLM(sm.families.Gaussian(sm.families.links.log), add_constant=False), 
                                  ProbaPredictingEstimator(ThresholdClassifier(HazardToRiskEstimator(LogisticRegression()))))

    model1 = CrossValidatingEstimator(ColumnSubsetTransformer(x_cols=best_subset) >> basic_model, metric=log_loss_metric)
    model2 = CrossValidatingEstimator(ColumnSubsetTransformer(x_cols=worst_subset) >> basic_model, metric=log_loss_metric)
    
    model = ModelSelector([model1, model2])
    
    model.fit(X, rate, exposure=exposure)
    np.testing.assert_array_equal(model.best_estimator_.estimator_.intermediate_stages_[0].x_cols, best_subset)

def test_cross_validating_estimator():
    np.random.seed(1)
    
    m = 1000
    n = 5
    
    X = np.random.normal(size=(m,n))
    beta = np.random.normal(size=(n,1))
    y = np.ravel(np.dot(X, beta)) + np.random.normal(.5, size=m)
    
    model = CrossValidatingEstimator(LinearRegression(), cv=KFold(n_splits=4, shuffle=True), n_jobs=2)
    
    y_pred_cv = model.fit_predict(X, y)
    
    y_pred = model.predict(X)
    
    assert r2_score(np.ravel(y_pred_cv), np.ravel(y_pred)) > .98
    

def test_non_null_row_subset_fitter():
    np.random.seed(1)
    
    m = 10000
    n = 10
    
    # Simulate an event under constant hazard, with hazard = X * beta and 
    # iid exponentially distributed exposure times.
    X = np.random.normal(size=(m,n))
    beta = np.random.normal(size=(n,1))
    y = np.ravel(np.dot(X, beta))
    
    missing = np.random.binomial(p=.001, n=1, size=(m,n)) == 1
    X[missing] = None
    
    model = NonNullSubsetFitter(LinearRegression())
    model.fit(X, y)
    assert np.max(np.abs(np.ravel(beta) - model.estimator_.coef_)) < .001

def test_linear_transformation():
    np.random.seed(1)
    
    m = 10000
    n = 10

    X = np.random.normal(size=(m,n))
    beta1 = np.random.normal(size=(n,1))
    y1 = np.ravel(np.dot(X, beta1))
    
    beta2 = np.random.normal(size=(n,1))
    y2 = np.ravel(np.dot(X, beta2))
    
    model1 = (Earth() >> LinearRegression()).fit(X, y1)
    model2 = Earth().fit(X, y2)
    
    combination = 2*model1 - model2
    
    assert_array_almost_equal(combination.predict(X), 2 * np.ravel(model1.predict(X)) - np.ravel(model2.predict(X)))

if __name__ == '__main__':
    import sys
    import nose
    # This code will run the test in this file.'
    module_name = sys.modules[__name__].__file__

    result = nose.run(argv=[sys.argv[0],
                            module_name,
                            '-s', '-v'])
    
    