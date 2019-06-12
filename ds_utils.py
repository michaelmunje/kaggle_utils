from scipy.stats import skew
from scipy.special import boxcox1p
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
import pandas as pd
import numpy as np


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
    proportion_nan = [sum(df[x].isnull()) / len(df[x]) for x, y in contains_nan]
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
    :return: None
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
    :return: None
    """
    cols = df[df.columns].corr().columns
    if df[col_to_correlate].dtype.name == 'category':
        df[col_to_correlate] = df[col_to_correlate].cat.codes
    corrs = df[df.columns].corr()[col_to_correlate]
    for col, corr in zip(cols, corrs):
        if abs(corr) > moderate_value and col != col_to_correlate:
            print(col, ': ', corr)


def remove_weak_correlations(df: pd.DataFrame, col_to_correlate: str, weak_threshold: float = 0.05) -> pd.DataFrame:
    """
    Removes weak correlation
    :param df: pandas DataFrame to remove columns from.
    :param col_to_correlate: String column name to check correlation with
    :param weak_threshold: float number that counts as an absolute weak threshold
    :return: pandas DataFrame without the columns weakly correlated to target
    """
    cols = df[df.columns].corr().columns
    corrs = df[df.columns].corr()[col_to_correlate]
    weakly_correlated = list()
    for col, corr in zip(cols, corrs):
        if abs(corr) < weak_threshold and col != col_to_correlate:
            weakly_correlated.append(col)
    return df.drop(columns=weakly_correlated)


def convert_categorical_to_numbers(to_change_df: pd.DataFrame, numbers: bool = True) -> pd.DataFrame:
    for col, dtype in zip(to_change_df.columns, to_change_df.dtypes):
        if dtype == object:
            to_change_df[col] = to_change_df[col].astype('category')
    if numbers:
        return pd.get_dummies(to_change_df)
    else:
        return to_change_df


def replace_missing_with_ml(df: pd.DataFrame, predict_missing_df: pd.DataFrame,
                            col_to_predict: str, is_classify: bool = False) -> (pd.DataFrame, pd.DataFrame):
    predict_missing_df[col_to_predict] = df[col_to_predict]
    adjusted_missing = predict_missing_df[predict_missing_df[col_to_predict].isnull() == False]

    y = adjusted_missing[col_to_predict].values
    x = adjusted_missing.drop(columns=[col_to_predict]).values

    x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=42)

    if is_classify:
        rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=42)
    else:
        rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=5, random_state=42)

    rf.fit(x_train, y_train)
    r2 = r2_score(y_test, rf.predict(x_test))
    mse = mean_squared_error(y_test, rf.predict(x_test))
    rmse = mse ** (1 / 2)
    print('R2          : ', round(r2, 4))
    print('RMSE        : ', round(rmse, 2))

    missing_df = predict_missing_df[predict_missing_df[col_to_predict].isnull()]
    x_missing = missing_df.drop(columns=[col_to_predict]).values
    predictions = rf.predict(x_missing).astype(int)

    df.loc[df[col_to_predict].isnull(), col_to_predict] = predictions

    predict_missing_df = predict_missing_df.drop(columns=[col_to_predict])
    return df, predict_missing_df


def remove_constant_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, df.apply(pd.Series.nunique) != 1]


def adjust_skewness(df: pd.DataFrame) -> pd.DataFrame:

    numerics = list()

    for col, dtype in zip(df.columns, df.dtypes):
        if dtype.name != 'object' and dtype.name != 'category':
            numerics.append(col)

    skewed_feats = df[numerics].apply(lambda x: skew(x.dropna())).sort_values(ascending=False)
    skewness = pd.DataFrame({'Skew': skewed_feats})
    skewness = skewness[abs(skewness) > 0.7]

    skewed_features = skewness.index
    lam = 0.15
    for feat in skewed_features:
        boxcot_trans = boxcox1p(df[feat], lam)
        if not boxcot_trans.isnull().any():
            df[feat] = boxcox1p(df[feat], lam)

    return df
