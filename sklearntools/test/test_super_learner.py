from sklearn.datasets.base import load_boston
from sklearntools.super_learner import SuperLearner
from sklearn.linear_model.base import LinearRegression
from pyearth import Earth
from sklearn.ensemble.forest import RandomForestRegressor
from sklearn.metrics.regression import r2_score
from sklearntools.kfold import CrossValidatingEstimator
import numpy as np
from sklearn2code.sklearn2code import sklearn2code
from sklearn2code.languages import numpy_flat
from sklearn2code.utility import exec_module
import pandas
from numpy.ma.testutils import assert_array_almost_equal
from toolz.itertoolz import first

def test_super_learner():
    np.random.seed(0)
    X, y = load_boston(return_X_y=True)
    X = pandas.DataFrame(X, columns=['x%d'%i for i in range(X.shape[1])])
    model = CrossValidatingEstimator(SuperLearner([('linear', LinearRegression()), ('earth', Earth(max_degree=2))],
                         LinearRegression(), cv=5, n_jobs=1), cv=5)
    cv_pred = model.fit_predict(X, y)
    pred = model.predict(X)
    cv_r2 = r2_score(y, cv_pred)
    best_component_cv_r2 = max([r2_score(y, first(model.estimator_.cross_validating_estimators_.values()).cv_predictions_) for i in range(2)])
    assert cv_r2 >= .9*best_component_cv_r2
    
    code = sklearn2code(model, ['predict'], numpy_flat)
    module = exec_module('module', code)
    test_pred = module.predict(**X)
    try:
        assert_array_almost_equal(np.ravel(pred), np.ravel(test_pred))
    except:
        idx = np.abs(np.ravel(pred) - np.ravel(test_pred)) > .000001
        print(np.ravel(pred)[idx])
        print(np.ravel(test_pred)[idx])
        raise
    print(r2_score(y, pred))
    print(r2_score(y, cv_pred))
    
    print(max([r2_score(y, first(model.estimator_.cross_validating_estimators_.values()).cv_predictions_) for i in range(2)]))


if __name__ == '__main__':
    import sys
    import nose
    # This code will run the test in this file.'
    module_name = sys.modules[__name__].__file__

    result = nose.run(argv=[sys.argv[0],
                            module_name,
                            '-s', '-v'])
