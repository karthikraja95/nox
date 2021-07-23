import inspect
import multiprocessing as mp
import os
import pickle
import warnings
from functools import partial, wraps
from pathlib import Path

import lightgbm as lgb
import matplotlib.pyplot as plt


with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=DeprecationWarning)

    import mlflow
    import mlflow.lightgbm
    import mlflow.sklearn
    import mlflow.xgboost

import xgboost as xgb
from sklearn.model_selection import GridSearchCV, KFold, StratifiedKFold
from yellowbrick.model_selection import CVScores, LearningCurve

from nyx.config import EXP_DIR, DEFAULT_MODEL_DIR, IMAGE_DIR, cfg
from nyx.config.config import _global_config
from nyx.util import _make_dir
from pickle import dump

def add_to_queue(model_function):
    @wraps(model_function)
    def wrapper(self, *args, **kwargs):
        default_kwargs = get_default_args(model_function)

        kwargs["run"] = kwargs.get("run", default_kwargs["run"])
        kwargs["model_name"] = kwargs.get("model_name", default_kwargs["model_name"])
        cv = kwargs.get("cv", False)

        if not _validate_model_name(self, kwargs["model_name"]):
            raise AttributeError("Invalid model name. Please choose another one.")

        if kwargs["run"]:
            return model_function(self, *args, **kwargs)
        else:
            if "XGBoost" in model_function.__name__:
                print(
                    "XGBoost is not comptabile to be run in parallel. Please run it normally or in run all models in a series."
                )
            else:
                kwargs["run"] = True
                self._queued_models[kwargs["model_name"]] = partial(
                    getattr(self, model_function.__name__), *args, **kwargs
                )

    return wrapper

def get_default_args(func):
    """
    Gets default arguments from a function.
    """

    signature = inspect.signature(func)

    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }

def run_gridsearch(model, gridsearch, cv=5, scoring="accuracy", **gridsearch_kwargs):
    """
    Runs Gridsearch on a model
    
    Parameters
    ----------
    model : Model
        Model to run gridsearch on
    gridsearch : dict
        Dict of params to test
    cv : int, Crossvalidation Generator, optional
        Cross validation method, by default 12
    
    scoring : str
        Scoring metric to use when evaluating models
    
    Returns
    -------
    Model
        Initialized Gridsearch model
    """

    if isinstance(gridsearch, dict):
        gridsearch_grid = gridsearch
        print(f"Gridsearching with the following parameters: {gridsearch_grid}")
    else:
        raise ValueError("Invalid Gridsearch input.")

    model = GridSearchCV(
        model, gridsearch_grid, cv=cv, scoring=scoring, **gridsearch_kwargs
    )

    return model

def run_crossvalidation(
    model, x_train, y_train, cv=5, scoring="accuracy", model_name=None
):
    """
    Runs cross validation on a certain model.
    
    Parameters
    ----------
    model : Model
        Model to cross validate
    x_train : nd-array
        Training data
    y_train : nd-array
        Testing data
    cv : int, Crossvalidation Generator, optional
        Cross validation method, by default 5
    scoring : str, optional
        Scoring method, by default 'accuracy'
    """

    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(15, 5))
    visualizer_scores = CVScores(model, cv=cv, scoring=scoring, ax=axes[0])
    visualizer_scores.fit(x_train, y_train)
    visualizer_scores.finalize()

    visualizer_lcurve = LearningCurve(model, cv=cv, scoring=scoring, ax=axes[1])
    visualizer_lcurve.fit(x_train, y_train)
    visualizer_lcurve.finalize()

    visualizer_scores.show()
    visualizer_lcurve.show()

    if _global_config["track_experiments"]:  # pragma: no cover
        fig.savefig(os.path.join(IMAGE_DIR, model_name, "cv.png"))

def _run_models_parallel(model_obj):
    """
    Runs queued models in parallel
    
    Parameters
    ----------
    model_obj : Model
        Model object
    """

    with mp.Pool(mp.cpu_count()) as pool:
        results = pool.map(_run, list(model_obj._queued_models.values()))

    for result in results:
        model_obj._models[result.model_name] = result
        del model_obj._queued_models[result.model_name]

    return results

def _run(model):
    """
    Runs a model
        
    Returns
    -------
    Model
        Trained model
    """

    return model()

def _get_cv_type(cv_type, n_splits, shuffle, **kwargs):
    """Takes in cv type from the user and initiates the cross validation generator."""

    n_splits = n_splits
    shuffle = shuffle

    if cv_type == "kfold":
        cv_type = KFold(n_splits=n_splits, shuffle=shuffle, random_state=42, **kwargs)
    elif cv_type == "strat-kfold":
        cv_type = StratifiedKFold(
            n_splits=n_splits, shuffle=shuffle, random_state=42, **kwargs
        )
    else:
        raise ValueError("Cross Validation type is invalid.")

    return cv_type