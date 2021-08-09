import copy
import os
import re

import ipywidgets as widgets
import numpy as np
import pandas as pd

from nyx.config import shell
from nyx.stats.stats import Stats
from nyx.util import (
    CLEANING_CHECKLIST,
    DATA_CHECKLIST,
    ISSUES_CHECKLIST,
    MULTI_ANALYSIS_CHECKLIST,
    PREPARATION_CHECKLIST,
    UNI_ANALYSIS_CHECKLIST,
    _get_columns,
    _get_attr_,
    _get_item_,
    _interpret_data,
    label_encoder,
)
from nyx.visualizations.visualizations import Visualizations
from IPython import get_ipython
from IPython.display import HTML, display
from ipywidgets import Layout


class Analysis(Visualizations, Stats):
    """
    Core class thats run analytical techniques.
    Parameters
    -----------
    x_train: pd.DataFrame
        Training data or aethos data object
    x_test: pd.DataFrame
        Test data, by default None
    target: str
        For supervised learning problems, the name of the column you're trying to predict.
    """

    def __init__(
        self, x_train, x_test=None, target="",
    ):

        self.x_train = x_train
        self.x_test = x_test
        self.target = target
        self.target_mapping = None

    def __repr__(self):

        return self.x_train.head().to_string()

    def _repr_html_(self):  # pragma: no cover

        if self.target:
            cols = self.features + [self.target]
        else:
            cols = self.features

        return self.x_train[cols].head()._repr_html_()

    def __getitem__(self, column):
        return _get_item_(self, column)

    def __getattr__(self, key):
        return _get_attr_(self, key)


    def __deepcopy__(self, memo):

        x_test = self.x_test.copy() if self.x_test is not None else None

        new_inst = type(self)(
            x_train=self.x_train.copy(), x_test=x_test, target=self.target,
        )

        new_inst.target_mapping = self.target_mapping

        return new_inst

    @property
    def features(self):
        """Features for modelling"""

        cols = self.x_train.columns.tolist()

        if self.target:
            cols.remove(self.target)

        return cols

    @property
    def y_test(self):
        """
        Property function for the testing predictor variable
        """

        if self.x_test is not None:
            if self.target:
                return self.x_test[self.target]
            else:
                return None
        else:
            return None

    @y_test.setter
    def y_test(self, value):
        """
        Setter function for the testing predictor variable
        """

        if self.x_test is not None:
            if self.target:
                self.x_test[self.target] = value
            else:
                self.target = "label"
                self.x_test["label"] = value
                print('Added a target (predictor) field (column) named "label".')


    @property
    def y_train(self):
        """
        Property function for the training predictor variable
        """

        return self.x_train[self.target] if self.target else None

    @y_train.setter
    def y_train(self, value):
        """
        Setter function for the training predictor variable
        """

        if self.target:
            self.x_train[self.target] = value
        else:
            self.target = "label"
            self.x_train["label"] = value
            print('Added a target (predictor) field (column) named "label".')

    @property
    def columns(self):
        """
        Property to return columns in the dataset.
        """

        return self.x_train.columns.tolist()

    @property
    def missing_values(self):
        """
        Property function that shows how many values are missing in each column.
        """

        dataframes = list(
            filter(lambda x: x is not None, [self.x_train, self.x_test,],)
        )

        missing_df = []
        for ind, dataframe in enumerate(dataframes):
            caption = (
                "Train set missing values." if ind == 0 else "Test set missing values."
            )

            if not dataframe.isnull().values.any():
                print("No missing values!")  # pragma: no cover
            else:
                total = dataframe.isnull().sum().sort_values(ascending=False)
                percent = (
                    dataframe.isnull().sum() / dataframe.isnull().count()
                ).sort_values(ascending=False)
                missing_data = pd.concat(
                    [total, percent], axis=1, keys=["Total", "Percent"]
                )

                missing_df.append(
                    missing_data.style.format({"Percent": "{:.2%}"}).set_caption(
                        caption
                    )
                )


        def multi_table(table_list):
            """ Acceps a list of IpyTable objects and returns a table which contains each IpyTable in a cell
            """
            return HTML(
                '<table><tr style="background-color:white;">'
                + "".join(
                    [
                        "<td style='padding-right:25px'>"
                        + table._repr_html_()
                        + "</td>"
                        for table in table_list
                    ]
                )
                + "</tr></table>"
            )

        if shell == "ZMQInteractiveShell":
            display(multi_table(missing_df))
        else:
            for table in missing_df:
                print(table)

    def copy(self):
        """
        Returns deep copy of object.
        
        Returns
        -------
        Object
            Deep copy of object
        """

        return copy.deepcopy(self)

    def standardize_column_names(self):
        """
        Utility function that standardizes all column names to lowercase and underscores for spaces.
        Returns
        -------
        Data:
            Returns a deep copy of the Data object.
        Examples
        --------
        >>> data.standardize_column_names()
        """

        new_column_names = {}
        pattern = re.compile("\W+")

        for name in self.x_train.columns:
            new_column_names[name] = re.sub(pattern, "_", name.lower())

        if self.target is not None:
            self.target = re.sub(pattern, "_", self.target.lower())

        self.col_mapping = new_column_names

        self.x_train.rename(columns=new_column_names, inplace=True)

        if self.x_test is not None:
            self.x_test.rename(columns=new_column_names, inplace=True)

        return self

    def expand_json_column(self, col):
        """
        Utility function that expands a column that has JSON elements into columns, where each JSON key is a column. 
        Parameters
        ----------
        cols: str
            Column in the data that has the nested data.
        Returns
        -------
        Data:
            Returns a deep copy of the Data object.
        Examples
        --------
        >>> data.expand_json_column('col1')
        """

        from pandas.io.json import json_normalize

        df = json_normalize(self.x_train[col], sep="_")
        self.x_train.drop(col, axis=1, inplace=True)
        self.x_train = pd.concat([self.x_train, df], axis=1)

        if self.x_test is not None:
            df = json_normalize(self.x_test[col], sep="_")
            self.x_test.drop(col, axis=1, inplace=True)
            self.x_test = pd.concat([self.x_test, df], axis=1)

        return self

    def data_report(self, title="Profile Report", output_file="", suppress=False):
        """
        Generates a full Exploratory Data Analysis report using Pandas Profiling.
        Credits: https://github.com/pandas-profiling/pandas-profiling
        
        For each column the following statistics - if relevant for the column type - are presented in an interactive HTML report:
        - Essentials: type, unique values, missing values
        - Quantile statistics like minimum value, Q1, median, Q3, maximum, range, interquartile range
        - Descriptive statistics like mean, mode, standard deviation, sum, median absolute deviation, coefficient of variation, kurtosis, skewness
        - Most frequent values
        - Histogram
        - Correlations highlighting of highly correlated variables, Spearman, Pearson and Kendall matrices
        - Missing values matrix, count, heatmap and dendrogram of missing values
        
        Parameters
        ----------
        title : str, optional
            Title of the report, by default 'Profile Report'
        output_file : str, optional
            File name of the output file for the report, by default ''
        suppress : bool, optional
            True if you do not want to display the report, by default False
        
        Returns
        -------
        HTML display of Exploratory Data Analysis report
        Examples
        --------
        >>> data.data_report()
        >>> data.data_report(title='Titanic EDA', output_file='titanic.html')
        """

        import pandas_profiling

        if shell == "ZMQInteractiveShell":  # pragma : no cover
            report = self.x_train.profile_report(
                title=title, html={"style": {"full_width": True}}
            )
        else:
            report = self.x_train.profile_report(title=title)

        if output_file:
            report.to_file(output_file=output_file)

        if not suppress:
            return report

    def describe(self, dataset="train"):
        """
        Describes your dataset using the DataFrameSummary library with basic descriptive info.
        Extends the DataFrame.describe() method to give more info.
        Credits go to @mouradmourafiq for his pandas-summary library.
        
        Parameters
        ----------
        dataset : str, optional
            Type of dataset to describe. Can either be `train` or `test`.
            If you are using the full dataset it will automatically describe
            your full dataset no matter the input, 
            by default 'train'
        
        Returns
        -------
        DataFrame
            Dataframe describing your dataset with basic descriptive info
        Examples
        ---------
        >>> data.describe()
        """

        from pandas_summary import DataFrameSummary

        if dataset == "train":
            x_train_summary = DataFrameSummary(self.x_train)

            return x_train_summary.summary()
        else:
            x_test_summary = DataFrameSummary(self.x_test)

            return x_test_summary.summary()

    def column_info(self, dataset="train"):
        """
        Describes your columns using the DataFrameSummary library with basic descriptive info.
        Credits go to @mouradmourafiq for his pandas-summary library.
        Info
        ----
        counts
        uniques
        missing
        missing_perc
        types
        
        Parameters
        ----------
        dataset : str, optional
            Type of dataset to describe. Can either be `train` or `test`.
            If you are using the full dataset it will automatically describe
            your full dataset no matter the input, 
            by default 'train'
        
        Returns
        -------
        DataFrame
            Dataframe describing your columns with basic descriptive info
        Examples
        ---------
        >>> data.column_info()
        """

        from pandas_summary import DataFrameSummary

        if dataset == "train":
            x_train_summary = DataFrameSummary(self.x_train)

            return x_train_summary.columns_stats
        else:
            x_test_summary = DataFrameSummary(self.x_test)

            return x_test_summary.columns_stats

    def describe_column(self, column, dataset="train"):
        """
        Analyzes a column and reports descriptive statistics about the columns.
        Credits go to @mouradmourafiq for his pandas-summary library.
        Statistics
        ----------
        std                                      
        max                                      
        min                                      
        variance                                 
        mean
        mode                                     
        5%                                       
        25%                                      
        50%                                      
        75%                                      
        95%                                      
        iqr                                      
        kurtosis                                 
        skewness                                 
        sum                                      
        mad                                      
        cv                                       
        zeros_num                                
        zeros_perc                               
        deviating_of_mean                        
        deviating_of_mean_perc                   
        deviating_of_median                      
        deviating_of_median_perc                 
        top_correlations                         
        counts                                   
        uniques                                  
        missing                                  
        missing_perc                             
        types                            
        
        Parameters
        ----------
        column : str
            Column in your dataset you want to analze.
        dataset : str, optional
            Type of dataset to describe. Can either be `train` or `test`.
            If you are using the full dataset it will automatically describe
            your full dataset no matter the input, 
            by default 'train'
        
        Returns
        -------
        dict
            Dictionary mapping a statistic and its value for a specific column
            
        Examples
        --------
        >>> data.describe_column('col1')
        """

        from pandas_summary import DataFrameSummary

        if dataset == "train":
            x_train_summary = DataFrameSummary(self.x_train)

            return x_train_summary[column]
        else:
            x_test_summary = DataFrameSummary(self.x_test)

            return x_test_summary[column]