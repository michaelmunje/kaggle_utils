import pandas as pd
from scipy.stats import skew
from scipy.special import boxcox1p
import sklearn
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import mean_squared_error
from sklearn.metrics import accuracy_score
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import numpy as np


def rank_features(X, Y, classify=True, plot=False, columns=None):

    if classify:
        forest = ExtraTreesClassifier(n_estimators=250,
                                    random_state=1337)
    else:
        forest = ExtraTreesRegressor(n_estimators=250,
                            random_state=1337)

    forest.fit(X, Y)
    importances = forest.feature_importances_
    std = np.std([tree.feature_importances_ for tree in forest.estimators_], axis=0)
    indices = np.argsort(importances)[::-1]

    print("Feature ranking:")

    if columns is None:
        for i in range(X.shape[1]):
            print(f"Feature {indices[i]}\t : {round(importances[indices[i]], 2)}")
    else:
        for i in range(X.shape[1]):
            print(f"{columns[indices[i]]}\t : {round(importances[indices[i]], 2)}")

    if plot:
        plt.figure()
        plt.title("Feature importances")
        plt.bar(range(X.shape[1]), importances[indices], color="b", yerr=std[indices], align="center")
        labels = indices if columns is None else columns
        plt.xticks(range(X.shape[1]), [columns[indices[i]] for i in range(X.shape[1])])
        plt.xlim([-1, X.shape[1]])
        fig = plt.gcf()
        fig.set_size_inches(8, 8)
        plt.show()


def adjust_skewness(df: pd.DataFrame, specific: str = None) -> pd.DataFrame:
    """
    Adjusts the skewness of all columns by finding highly skewed columns
    and performing a boxcox transformation
    :param df: pandas DataFrame to adjust skewed columns in
    :return: pandas DataFrame with skew adjusted columns
    """

    numerics = list(x[0] for x in (filter(lambda x: x[1].name != 'object' and x[1].name != 'category', zip(df.columns, df.dtypes))))
    skewed_feats = df[numerics].apply(lambda x: skew(x.dropna())).sort_values(ascending=False)
    skewness = pd.DataFrame({'Skew': skewed_feats})
    skewness = skewness[abs(skewness) > 0.7]
    skewed_features = skewness.index
    if specific:
        skewed_features = [specific]
    lam = 0.15

    for feat in skewed_features:
        boxcot_trans = boxcox1p(df[feat], lam)
        if not boxcot_trans.isnull().any():
            df[feat] = boxcox1p(df[feat], lam)

    return df


def get_nan_col_proportions(df: pd.DataFrame, lowest_proportion: float = 0.0) -> [(str, float)]:
    """
    Prints out all columns with NaN values that exceed a specific proportion (default 0.0)
    :param df: pandas DataFrame to look into.
    :param lowest_proportion: float that is the lowest proportions that we print.
    :return: None
    """

    values = list(zip(list(df.isnull().columns), list(df.isnull().any())))
    filtered = list(filter(lambda x: x[1][1] == True, enumerate(values)))
    contains_nan = [y for x, y in filtered]
    proportion_nan = [round(sum(df[x].isnull()) / len(df[x]), 3) for x, y in contains_nan]
    proportion_nan = [(x[0], proportion_nan[i]) for i, x in enumerate(contains_nan)]
    nan_prop_list = list()
    for col, propo_nan in proportion_nan:
        if abs(propo_nan) > lowest_proportion:
            nan_prop_list.append((col, propo_nan))
    return nan_prop_list


def remove_nan_cols(df: pd.DataFrame, prop_threshold: float = 0.0) -> pd.DataFrame:
    """
    Prints out all columns with NaN values that exceed a specific proportion (default 0.0)
    :param df: pandas DataFrame to look into.
    :param prop_threshold: float that is the lowest proportion that we delete
    :return: pandas DataFrame with removed nans
    """

    nan_props = get_nan_col_proportions(df, prop_threshold)
    names = [name for name, _ in nan_props]
    df.drop(columns=names, inplace=True)
    return df


def print_moderate_correlations(df: pd.DataFrame, col_to_correlate: str, moderate_value: float = 0.4) -> None:
    """
    Prints out all correlations deemed as moderate (0.4, or set by parameter).
    :param df: pandas DataFrame to look into.
    :param col_to_correlate: String that represents column we want to check correlations with.
    :param moderate_value: Which correlation value we deem as moderate (default 0.4).
    """

    if df[col_to_correlate].dtype.name == 'category':
        df[col_to_correlate] = df[col_to_correlate].cat.codes
    corrs = df[df.columns].corr()
    cols = corrs.columns
    corrs_value = corrs[col_to_correlate]
    for col, corr_value in zip(cols, corrs_value):
        if abs(corr_value) > moderate_value and col != col_to_correlate:
            print(col, ' : ', round(corr_value, 2))


def remove_weak_correlations(df1: pd.DataFrame, df2, y, weak_threshold: float = 0.1) -> (pd.DataFrame, pd.DataFrame):
    """
    Removes weak correlations
    :param df: pandas DataFrame to remove columns from.
    :param col_to_correlate: String column name to check correlation with
    :param weak_threshold: float number that counts as an absolute weak threshold
    :return: pandas DataFrame without the columns weakly correlated to target
    """
    col_to_correlate = 'PREDICTOR_TO_CHECK_WEAK_CORRS'
    df1[col_to_correlate] = y
    cols = df1[df1.columns].corr().columns
    corrs = df1[df1.columns].corr()[col_to_correlate]
    strongly_correlated = list()
    for col, corr in zip(cols, corrs):
        if abs(corr) >= weak_threshold and col != col_to_correlate:
            strongly_correlated.append(col)
    df1 = df1.drop(columns=[col_to_correlate])
    for col in df1.columns:
        if col not in strongly_correlated:
            df1.drop(columns=[col], inplace=True)
            df2.drop(columns=[col], inplace=True)
    return df1, df2
              

def remove_constant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes all redundant columns which have the same value across the column
    :param df: pandas DataFrame to remove redundant columns from
    :return: pandas DataFrame without redundant columns
    """

    return df.loc[:, df.apply(pd.Series.nunique) != 1]


def convert_categorical_to_numbers(to_change_df: pd.DataFrame) -> pd.DataFrame:
    """
    Dummifies all category data including objects.
    Assumes the data has been cleaned and the dtypes are consistent.
    :param to_change_df: pandas DataFrame to convert to all numerical
    :return: Dummified input pandas DataFrame
    """
    return pd.get_dummies(convert_objects_to_categories(to_change_df))


def convert_objects_to_categories(to_change_df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts all object dtypes into categories
    :param to_change_df: pandas DataFrame to convert objects to categories
    :return: pandas DataFrame with categories instead of objects
    """

    for col, dtype in zip(to_change_df.columns, to_change_df.dtypes):
        if dtype == object:
            to_change_df[col] = to_change_df[col].astype('category')
    return to_change_df


def replace_missing_with_ml(df: pd.DataFrame, col_to_predict: str) -> None:
    """
    Replace the missing values in the given column using machine learning predictions
    :param df: pandas DataFrame to use as features (and predictor column)
    :param col_to_predict: string that represents the predictor column
    :return: pandas DataFrame with filled predictor column values via machine learning
    """

    y = df[col_to_predict].values

    dummified_df = df.copy()

    cols_to_drop = filter(lambda t: t[1], zip(df.columns, df.isnull().any()))
    cols_to_drop = list(x[0] for x in cols_to_drop)

    dummified_df = dummified_df.drop(columns=cols_to_drop)
    dummified_df = convert_categorical_to_numbers(dummified_df)

    dummified_df[col_to_predict] = y

    df_to_model = dummified_df.dropna(subset=[col_to_predict])

    df_to_predict = dummified_df[dummified_df[col_to_predict].isnull()]
    df_to_predict = df_to_predict.drop(columns=[col_to_predict])

    y = df_to_model[col_to_predict]
    x = df_to_model.drop(columns=[col_to_predict]).values

    x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=1337)

    is_classify = True

    if df[col_to_predict].dtype.name == 'object':
        rf = GradientBoostingClassifier(n_estimators=3000, learning_rate=0.05,
                                        max_depth=4, max_features='sqrt',
                                        min_samples_leaf=15, min_samples_split=10)
    else:
        is_classify = False
        rf = GradientBoostingRegressor(n_estimators=3000, learning_rate=0.05,
                                       max_depth=4, max_features='sqrt',
                                       min_samples_leaf=15, min_samples_split=10,
                                       loss='huber')

    rf.fit(x_train, y_train)

    print("Successfully trained feature engineering model to predict: " + col_to_predict)
    print("------Evaluation-------")

    if is_classify:
        acc = accuracy_score(y_test, rf.predict(x_test))
        print('ACC         : ', round(acc, 4))
    else:
        r2 = r2_score(y_test, rf.predict(x_test))
        mse = mean_squared_error(y_test, rf.predict(x_test))
        rmse = mse ** (1 / 2)
        print('R2          : ', round(r2, 4))
        print('RMSE        : ', round(rmse, 2))

    df.loc[df[col_to_predict].isnull(), col_to_predict] = rf.predict(df_to_predict.values)


def apply_scale(x_train: np.array, x_test: np.array, scale_type: str = 'Standard') -> (np.array, np.array):
    """
    Scales the data according to the distribution of x_train
    :param x_train: numpy.array to scale via its distribution
    :param x_test: numpy.array to scale according to x_test's distribution
    :param scale_type: Which scaling type to use. Options: 'Standard', 'Robust', 'MinMax'. Default = 'Standard'
    :return: x_train and x_test properly scaled.
    """

    if scale_type == 'Standard':
        scaler = sklearn.preprocessing.StandardScaler()
    elif scale_type == 'Robust':
        scaler = sklearn.preprocessing.RobustScaler()
    elif scale_type == 'MinMax':
        scaler = sklearn.preprocessing.MinMaxScaler()
    else:
        raise Exception('Invalid string input for scale_type')

    scaler.fit(x_train) # Correct to use only the training data to not bias our model's test evaluation 
    return scaler.transform(x_train), scaler.transform(x_test)


def apply_pca(x_train: np.array, x_test: np.array, n_comps: float = 0.975) -> (np.array, np.array):
    """
    Apply PCA to the data according to the distribution of x_train
    :param x_train: numpy.array to scale via its distribution
    :param x_test: numpy.array to scale according to x_test's distribution
    :param n_comps: Either the number of principal components, or the variance to be kept in the components.
    :return: x_train and x_test with PCA applied.
    """

    pca = sklearn.decomposition.PCA(n_components=n_comps)
    pca.fit(x_train) # Correct to use only the training data to not bias our model's test evaluation
    return pca.transform(x_train), pca.transform(x_test)