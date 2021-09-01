[![PyPI version](https://badge.fury.io/py/fika.svg)](https://badge.fury.io/py/fika) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/fika) 

# Fika

*"A collection of tools for Data Scientists and ML Engineers to automate their workflow of performing analysis to deploying models and pipelines."*

Fika is a library/platform that automates your data science and analytical tasks at any stage in the pipeline. Fika is, at its core, a uniform API that helps automate analytical techniques from various libaries such as pandas, sci-kit learn, spacy, etc.

**Fika** in Swedish - *A moment to slow down and appreciate the good things in life*

## Analysis with Fika

```python
import fika as fk
import pandas as pd

x_train = pd.read_csv('https://raw.githubusercontent.com/karthikraja95/fika/master/examples/data/train.csv') # load data into pandas

# Initialize Data object with training data
# By default, if no test data (x_test) is provided, then the data is split with 20% going to the test set
# 
# Specify predictor field as 'Survived'
df = fk.Classification(x_train, target='Survived')

df.x_train # View your training data
df.x_test # View your testing data

df # Glance at your training data

df[df.Age > 25] # Filter the data

df.x_train['new_col'] = [1,2] # This is the exact same as the either of code above
df.x_test['new_col'] = [1,2]

df.data_report(title='Titanic Summary', output_file='titanic_summary.html') # Automate EDA with pandas profiling with an autogenerated report

df.describe() # Display a high level view of your data using an extended version of pandas describe

df.column_info() # Display info about each column in your data

df.describe_column('Fare') # Get indepth statistics about the 'Fare' column

df.mean() # Run pandas functions on the aethos objects

df.missing_values # View your missing data at anytime

df.correlation_matrix() # Generate a correlation matrix for your training data

df.predictive_power() # Calculates the predictive power of each variable

df.autoviz() # Runs autoviz on the data and runs EDA on your data

df.pairplot() # Generate pairplots for your training data features at any time

df.checklist() # Will provide an iteractive checklist to keep track of your cleaning tasks

```
**NOTE:** One of the benefits of using `fika` is that any method you apply on your train set, gets applied to your test dataset. For any method that requires fitting (replacing missing data with mean), the method is fit on the training data and then applied to the testing data to avoid data leakage.

```python
# Replace missing values in the 'Fare' and 'Embarked' column with the most common values in each of the respective columns.
df.replace_missing_mostcommon('Fare', 'Embarked')

# Replace missing values in the 'Age' column with a random value that follows the probability distribution of the 'Age' column in the training set. 
df.replace_missing_random_discrete('Age')

df.drop('Cabin') # Drop the cabin column
```

As you've started to notice, alot of tasks to df the data and to explore the data have been reduced down to one command, and are also customizable by providing the respective keyword arguments.


```python
# Create a barplot of the mean surivial rate grouped by age.
df.barplot(x='Age', y='Survived', method='mean')

# Plots a scatter plot of Age vs. Fare and colours the dots based off the Survived column.
df.scatterplot(x='Age', y='Fare', color='Survived')

# One hot encode the `Person` and `Embarked` columns and then drop the original columns
df.onehot_encode('Person', 'Embarked', keep_col=False) 

```

## Modelling with Fika

### Running a Single Model

Models can be trained one at a time or multiple at a time. They can also be trained by passing in the params for the sklearn, xgboost, etc constructor, by passing in a gridsearch dictionary & params, cross validating with gridsearch & params.

After a model has been ran, it comes with use cases such as plotting RoC curves, calculating performance metrics, confusion matrices, SHAP plots, decision tree plots and other local and global model interpretability use cases.

```python
lr_model = df.LogisticRegression() # Train a logistic regression model

# Train a logistic regression model with gridsearch
lr_model = df.LogisticRegression(gridsearch={'penalty': ['l1', 'l2']}, random_state=42)

# Crossvalidate a a logistic regression model, displays the scores and the learning curve and builds the model
lr_model = df.LogisticRegression()
lr_model.cross_validate(n_splits=10) # default is strat-kfold for classification  problems

# Build a Logistic Regression model with Gridsearch and then cross validates the best model using stratified K-Fold cross validation.
lr_model = model.LogisticRegression(gridsearch={'penalty': ['l1', 'l2']}, cv_type="strat-kfold") 

lr_model.help_debug() # Interface with items to check for to help debug your model.

lr_model.metrics() # Views all metrics for the model
lr_model.confusion_matrix()
lr_model.decision_boundary()
lr_model.roc_curve()
```

### Running multiple models in parallel

```python
# Add a Logistic Regression, Random Forest Classification and a XGBoost Classification model to the queue.
lr = df.LogisticRegression(random_state=42, model_name='log_reg', run=False)
rf = df.RandomForestClassification(run=False)


df.run_models() # This will run all queued models in parallel
df.run_models(method='series') # Run each model one after the other

df.compare_models() # This will display each model evaluated against every metric

# Every model is accessed by a unique name that is assiged when you run the model.
# Default model names can be seen in the function header of each model.

df.log_reg.confusion_matrix() # Displays a confusion matrix for the logistic regression model
df.rf_cls.confusion_matrix() # Displays a confusion matrix for the random forest model
```

## Model Interpretability

As mentioned in the Model section, whenever a model is trained you have access to use cases for model interpretability as well. There are prebuild SHAP usecases and an interactive dashboard that is equipped with LIME and SHAP for local model interpretability and Morris Sensitivity for global model interpretability.

```python
lr_model = model.LogisticRegression(random_state=42)

lr_model.summary_plot() # SHAP summary plot
lr_model.force_plot() # SHAP force plot
lr_model.decision_plot() # SHAP decision plot
lr_model.dependence_plot() # SHAP depencence plot

# Creates an interactive dashboard to interpret predictions of the model
lr_model.interpret_model() 
```

## Code Generation

Currently you are only able to export your model to be ran a service, and will be able to automatically generate the required files. The automatic creation of a data pipeline is still in progress.

```python

lr_model.to_service('titanic')
```

Now navigate to 'your_home_folder'('~' on linux and Users/'your_user_name' on windows)/.fika/projects/titanic/ and you will see the files needed to run the model as a service using FastAPI and uvicorn. 

## Setup

**Python Requirements**: 3.6, 3.7

RUN: `pip install fika`


## How to use Fika

Take a look at this [fika.ipynb](https://github.com/karthikraja95/fika/blob/master/examples/Fika.ipynb) notebook.

## For Developers

To install packages `pip3 install -r requirements-dev.txt`

