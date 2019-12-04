from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.ensemble import GradientBoostingClassifier
from sklearn import svm
from sklearn.model_selection import KFold
from sklearn.preprocessing import RobustScaler
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import RobustScaler
from sklearn.linear_model import Lasso
from sklearn.linear_model import ElasticNet
from sklearn.linear_model import HuberRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score
from sklearn.utils import shuffle
from scipy.optimize import minimize
import copy
from typing import Callable
import numpy as np


def evaluate_classifier(clf, x, y):
    scores = cross_val_score(clf, x, y, cv=5)
    print("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))
    

# def rank_features(X, Y):
#     forest = ExtraTreesClassifier(n_estimators=250,
#                                   random_state=0)
#     forest.fit(X, Y)
#     importances = forest.feature_importances_
#     std = np.std([tree.feature_importances_ for tree in forest.estimators_],
#                  axis=0)
#     indices = np.argsort(importances)[::-1]

#     # Print the feature ranking
#     print("Feature ranking:")

#     for f in range(X.shape[1]):
#         print("%d. feature %d (%f)" % (f + 1, indices[f], importances[indices[f]]))

#     # Plot the feature importances of the forest
#     plt.figure()
#     plt.title("Feature importances")
#     plt.bar(range(X.shape[1]), importances[indices],
#            color="r", yerr=std[indices], align="center")
#     plt.xticks(range(X.shape[1]), indices)
#     plt.xlim([-1, X.shape[1]])
#     plt.show()
#     return indices


def evaluate_regressor(y_actual: np.array, y_pred: np.array, metric_func: Callable[[np.array, np.array], float]) -> [float]:
    """
    Evaluates the prediction results of a regressor.
    :param y_actual: numpy array of actual values
    :param y_pred: numpy array of predicted values
    :param metric_func: custom function to evaluate. Default = None
    :return: Returns the evaluation metrics for the regressor.
    """

    r2 = r2_score(y_actual, y_pred)
    mse = mean_squared_error(y_actual, y_pred)
    rmse = mse ** (1 / 2)
    metrics = [r2, mse, rmse]

    print('R2          : ', round(r2, 4))
    print('MSE        : ', round(mse, 4))
    print('RMSE        : ', round(rmse, 4))

    if metric_func: 
        custom_metric = metric_func(y_actual, y_pred)
        metrics.append(custom_metric)
        print('CUSTOM METRIC: ', round(custom_metric, 4))

    return metrics


class RegressorModel:

    def __init__(self, model):
        self.model = model

    def predict(self, x):
        return self.model.predict(x)


def cross_validate(model, x: np.array, y: np.array, metric: Callable[[np.array, np.array], float], folds: int = 5,
                   repeats: int = 3, verbose: bool = True) -> float:
    """
    Perform k-fold cross-validation using the out of the bag score.
    :param model: scikit-learn like model to perform cross validation on
    :param x: numpy array of features
    :param y: numpy array of predictors
    :param metric: what metric to use to evaluate the models
    :param folds: number of folds. Default = 5.
    :param repeats: number of times to repeat the whole process (different random splitting). Default = 3.
    :param verbose: Whether to print progress messages. Default = True.
    :return: the average metric score across all folds and repeats
    """

    y_pred = np.zeros(len(y))
    score = np.zeros(repeats)

    for r in range(repeats):
        if verbose:
            print('Running k-fold cross-validation ', r + 1, '/', repeats)
        x, y = shuffle(x, y, random_state=r)

        for i, (train_ind, test_ind) in enumerate(KFold(n_splits=folds, random_state=r + 10).split(x)):
            if verbose:
                print('Computing fold ', i + 1, '/', folds)
            x_train, y_train = x[train_ind, :], y[train_ind]
            x_test, y_test = x[test_ind, :], y[test_ind]
            model.fit(x_train, y_train)
            y_pred[test_ind] = model.predict(x_test)
        score[r] = metric(y_pred, y)

    print('Evaluation metric:', metric.__name__)
    print('Average:', np.round(np.mean(score), 4))
    print('Std. Dev:', np.round(np.std(score), 4))
    mean = np.mean(score)
    return mean[0] if len(mean) > 1 else mean


class EnsembleRegressor:

    def __init__(self, models):
        self.models = models

    def predict(self, x: np.array) -> np.array:
        total = np.zeros(len(x))
        for model in self.models:
            total += model.predict(x)
        total /= len(self.models)
        return total


def get_cross_validation_models(model, x: np.array, y: np.array, metric: Callable[[np.array, np.array], float], folds: int = 5,
                   repeats: int = 3, verbose: bool = True) -> EnsembleRegressor:
    """
    Perform k-fold cross-validation using the out of the bag score.
    :param model: scikit-learn like model to perform cross validation on
    :param x: numpy array of features
    :param y: numpy array of predictors
    :param metric: what metric to use to evaluate the models
    :param folds: number of folds. Default = 5.
    :param repeats: number of times to repeat the whole process (different random splitting). Default = 3.
    :param verbose: Whether to print progress messages. Default = True.
    :return: the average metric score across all folds and repeats
    """

    y_pred = np.zeros(len(y))
    score = np.zeros(repeats)
    ensemble = EnsembleRegressor([])

    for r in range(repeats):
        if verbose:
            print('Running k-fold cross-validation ', r + 1, '/', repeats)
        x, y = shuffle(x, y, random_state=r)

        for i, (train_ind, test_ind) in enumerate(KFold(n_splits=folds, random_state=r + 10).split(x)):
            if verbose:
                print('Computing fold ', i + 1, '/', folds)
            x_train, y_train = x[train_ind, :], y[train_ind]
            x_test, y_test = x[test_ind, :], y[test_ind]
            model.fit(x_train, y_train)
            ensemble.models.append(copy.copy(model))
            y_pred[test_ind] = model.predict(x_test)
        score[r] = metric(y_pred, y)

    print('Evaluation metric:', metric.__name__)
    print('Average:', np.round(np.mean(score), 4))
    print('Std. Dev:', np.round(np.std(score), 4))

    return ensemble


def try_many_regressors(x: np.array, y: np.array, metric: Callable[[np.array, np.array], float],
                        metric_max_better: bool = True) -> None:
    """
    Tries a few solid regressors in sklearn and returns the best performing one
    :param x: numpy array of the features
    :param y: numpy array of the predictor
    :param metric: Function, the evaluation metric to use.
    :param metric_max_better: If the metric's higher value means better value
    """

    gb = GradientBoostingRegressor(n_estimators=3000, learning_rate=0.05,
                                   max_depth=4, max_features='sqrt',
                                   min_samples_leaf=15, min_samples_split=10,
                                   loss='huber', random_state=42)

    gb2 = GradientBoostingRegressor(learning_rate=0.05, max_features='sqrt', loss='huber',
                                    min_impurity_split=None, min_samples_leaf=15,
                                    min_samples_split=10, n_estimators=12000,
                                    random_state=42)

    lasso = make_pipeline(RobustScaler(), Lasso(alpha=0.0005, random_state=42))
    elastic = make_pipeline(RobustScaler(), ElasticNet(alpha=0.0005, l1_ratio=.9, max_iter=10000, random_state=42))
    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=3, random_state=42)
    rrf = ExtraTreesRegressor(n_estimators=200, min_samples_leaf=3, random_state=42)
    huber = HuberRegressor()
    linear = LinearRegression()
    nn = MLPRegressor(hidden_layer_sizes=(1000, 10), learning_rate='adaptive',
                      max_iter=1000, random_state=42, early_stopping=True)
    svm_r = svm.SVR(kernel='poly', gamma='auto')
    knn = KNeighborsRegressor(n_neighbors=5)

    regressors = [gb, gb2, lasso, elastic, rf, rrf, huber, linear, nn, svm_r, knn]
    scores = np.zeros(len(regressors))

    for i, r in enumerate(regressors):
        print('Running k-fold cross validation for', r.__class__.__name__)
        scores[i] = cross_validate(r, x, y, metric)

    best_index = np.argmax if metric_max_better else np.argmin
    best = np.amax if metric_max_better else np.amin
    first = lambda s: s[0] if len(s) > 1 else s

    print('Best performing model: ', regressors[first(best_index(scores))].__class__.__name__)
    print('Best', metric.__name__, ':', best(scores))



def get_ensembles_many_regressors(x: np.array, y: np.array, metric: Callable[[np.array, np.array], float],
                                  metric_max_better: bool = True) -> None:
    """
    Tries a few solid regressors in sklearn and returns the best performing one
    :param x: numpy array of the features
    :param y: numpy array of the predictor
    :param metric: Function, the evaluation metric to use.
    :param metric_max_better: If the metric's higher value means better value
    """

    gb = GradientBoostingRegressor(n_estimators=3000, learning_rate=0.05,
                                   max_depth=4, max_features='sqrt',
                                   min_samples_leaf=15, min_samples_split=10,
                                   loss='huber', random_state=42)

    gb2 = GradientBoostingRegressor(learning_rate=0.05, max_features='sqrt', loss='huber',
                                    min_impurity_split=None, min_samples_leaf=15,
                                    min_samples_split=10, n_estimators=12000,
                                    random_state=42)

    lasso = make_pipeline(RobustScaler(), Lasso(alpha=0.0005, random_state=42))
    elastic = make_pipeline(RobustScaler(), ElasticNet(alpha=0.0005, l1_ratio=.9, max_iter=10000, random_state=42))
    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=3, random_state=42)
    rrf = ExtraTreesRegressor(n_estimators=200, min_samples_leaf=3, random_state=42)
    huber = HuberRegressor()
    linear = LinearRegression()
    nn = MLPRegressor(hidden_layer_sizes=(1000, 10), learning_rate='adaptive',
                      max_iter=1000, random_state=42, early_stopping=True)
    svm_r = svm.SVR(kernel='poly', gamma='auto')
    knn = KNeighborsRegressor(n_neighbors=5)

    regressors = [gb, gb2, lasso, elastic, rf, rrf, huber, linear, nn, svm_r, knn]
    scores = np.zeros(len(regressors))

    for i, r in enumerate(regressors):
        print('Running k-fold cross validation for', r.__class__.__name__)
        scores[i] = cross_validate(r, x, y, metric)

    best_index = np.argmax if metric_max_better else np.argmin
    best = np.amax if metric_max_better else np.amin
    first = lambda s: s[0] if len(s) > 1 else s

    print('Best performing model: ', regressors[first(best_index(scores))].__class__.__name__)
    print('Best', metric.__name__, ':', best(scores))


def evaluate_ensemble_weights(weights: np.array, model_preds: np.array, y_test: np.array,
                          metric: Callable[[np.array, np.array], float], maximize: bool = True) -> float:
    """
    Computes the metric of the ensemble according to some weights
    :param weights: the weights of each model (their priority for the prediction)
    :param model_preds: the precomputed predictions of each model (cross validated predictions)
    :param y_test: numpy.array of true values
    :param metric: metric to evaluate ensemble
    :param maximize: if a higher score means better
    :return: the computed metric of the ensemble (or negative of it)
    """

    y_pred = sum(x * y for x, y in zip(model_preds, weights))
    return -1 * metric(y_test, y_pred) if maximize else metric(y_test, y_pred)


def optimize_ensemble(ensemble: EnsembleRegressor, x_test: np.array, y_test: np.array,
                      metric: Callable[[np.array, np.array], float], metric_max_better: bool = True) -> np.array:
    """
    Optimizes the weights in the ensemble model
    :param ensemble: The ensemble containing all the models
    :param x_test: numpy array of testing features
    :param y_test: numpy array of testing predictors
    :param metric: evaluation metric to optimize
    :param metric_max_better: if higher metric score means better
    :return: The optimized weights of the ensemble model
    """

    model_preds = np.array((model.predict(x_test) for model in ensemble.models))
    x0 = np.ones(len(model_preds))
    bounds = [(0, 1)] * len(x0)
    cons = {'type': 'eq', 'fun': lambda x: sum(x) - 1}

    optimized = minimize(evaluate_ensemble_weights, x0, bounds=bounds, constraints=cons,
                         args=(model_preds, y_test, metric, metric_max_better))

    return optimized.x


