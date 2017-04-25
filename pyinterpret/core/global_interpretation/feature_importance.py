"""Partial Dependence class"""
from itertools import product, cycle
import numpy as np
import pandas as pd

from .base import BaseGlobalInterpretation
from ...util.static_types import StaticTypes
from ...util import exceptions
from ...util.kernels import flatten
from ...util.plotting import COLORS
from ...util.exceptions import *

class FeatureImportance(BaseGlobalInterpretation):
    """Contains methods for feature importance. Subclass of BaseGlobalInterpretation"""

    @staticmethod
    def _build_fresh_metadata_dict():
        return {
            'pdp_cols': {},
            'sd_col':'',
            'val_cols':[]
        }


    def feature_importance(self, modelinstance):

        """
        Computes feature importance of all features related to a model instance.


        Parameters:
        -----------

        modelinstance: pyinterpret.model.model.Model subtype
            the machine learning model "prediction" function to explain, such that
            predictions = predict_fn(data).

            :Example:
            >>> from pyinterpret.model import InMemoryModel
            >>> from pyinterpret.core.explanations import Interpretation
            >>> from sklearn.ensemble import RandomForestClassier
            >>> rf = RandomForestClassier()
            >>> rf.fit(X,y)


            >>> model = InMemoryModel(rf, examples = X)
            >>> interpreter = Interpretation()
            >>> interpreter.load_data(X)
            >>> interpreter.feature_importance.feature_importance(model)

            Supports classification, multi-class classification, and regression.

        """

        importances = {}
        original_predictions = modelinstance.predict(self.data_set.data)

        n = original_predictions.shape[0]

        # instead of copying the whole dataset, should we copy a column, change column values,
        # revert column back to copy?
        for feature_id in self.data_set.feature_ids:
            X_mutable = self.data_set.data.copy()
            samples = self.data_set.generate_column_sample(feature_id, n_samples=n, method='random-choice')
            feature_perturbations = X_mutable[feature_id] - samples
            X_mutable[feature_id] = samples
            new_predictions = modelinstance.predict(X_mutable)
            changes_in_predictions = new_predictions - original_predictions
            importance = np.mean(np.std(changes_in_predictions, axis=0))
            importances[feature_id] = importance

        importances =  pd.Series(importances).sort_values()
        importances = importances / importances.sum()
        return importances


    def plot_feature_importance(self, predict_fn, ax=None):
        """Computes feature importance of all features related to a model instance,
        then plots the results.


        Parameters:
        -----------

        modelinstance: pyinterpret.model.model.Model subtype
            the machine learning model "prediction" function to explain, such that
            predictions = predict_fn(data).

            For instance:
            >>> from pyinterpret.model import InMemoryModel
            >>> from pyinterpret.core.explanations import Interpretation
            >>> from sklearn.ensemble import RandomForestClassier
            >>> rf = RandomForestClassier()
            >>> rf.fit(X,y)


            >>> model = InMemoryModel(rf, examples = X)
            >>> interpreter = Interpretation()
            >>> interpreter.load_data(X)
            >>> interpreter.feature_importance.feature_importance(model)

            Supports classification, multi-class classification, and regression.

        ax: matplotlib.axes._subplots.AxesSubplot
            existing subplot on which to plot feature importance. If none is provided,
            one will be created.
            """
        try:
            global pyplot
            from matplotlib import pyplot
        except ImportError:
            raise (MatplotlibUnavailableError("Matplotlib is required but unavailable on your system."))
        except RuntimeError:
            raise (MatplotlibDisplayError("Matplotlib unable to open display"))

        importances = self.feature_importance(predict_fn)

        if ax is None:
            f, ax = pyplot.subplots(1)
        else:
            f = ax.figure

        colors = cycle(COLORS)
        color = colors.next()
        importances.sort_values().plot(kind='barh',ax=ax, color=color)
