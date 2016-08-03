# Code is borrowed from this script: https://www.kaggle.com/users/213536/vasco/predict-west-nile-virus/west-nile-heatmap

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import callables as cl
from IPython.display import display

from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, make_scorer
from sklearn.cross_validation import cross_val_score, ShuffleSplit, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.cross_validation import ShuffleSplit
from sklearn.learning_curve import learning_curve

pd.set_option('display.max_columns', 50)

# Load data
train = pd.read_csv('../input/train.csv')
weather = pd.read_csv('../input/weather.csv', na_values=['M', '-', ' '])

# Get to know what's in the dataset
display(train.head(), train.shape)
display(weather.columns.values, weather.shape)

# Data Exploration
# Check the statistic of the training data
display(train.describe())
display(train.Species.unique())

# Exclude redundant columns from the training data
train_drop = ['Address', 'AddressNumberAndStreet', 'AddressAccuracy']
train = train.drop(train_drop, axis=1)

# Check data types
display(train.dtypes)
display(weather.dtypes)

# Tidy up the weather data
# Count the number of missing data by column
for column in weather.columns:
    print column, weather[column].isnull().values.sum()

# Count the number of missing data by station
print 1472 - weather.groupby('Station').count()

# Drop columns with high count of missing data in both stations and unimputable Station2 data
weather_drop = ['Water1', 'CodeSum']
weather = weather.drop(weather_drop, axis=1)

# Impute 'T' (trace) precipitation with zero
weather.replace('  T', 0.0, inplace=True)
# Convert PrecipTotal to real number
weather['PrecipTotal'] = weather['PrecipTotal'].astype(float)

# Impute missing data with median for: Tavg, WetBulb, Heat, Cool, PrecipTotal, StnPressure, SeaLevel, AvgSpeed
weather_impute = ['Tavg', 'WetBulb', 'Heat', 'Cool', 'PrecipTotal', 'StnPressure', 'SeaLevel', 'AvgSpeed']
# Data statistics before imputation
display(weather[weather_impute].describe())
for col in weather_impute:
    median = weather[col].median()
    weather[col].loc[weather[col].isnull()] = median
    
# Data statistics after imputation
display(weather[weather_impute].describe())

# Verify all missing data has been accounted for
for column in weather.columns:
    print column, weather[column].isnull().values.sum()

# First 5 rows of the final weather data
display(weather.head())

# Visualize locations on the map
cl.Map(train)

# Convert Date to datetime format and add Year & Month columns
files = [train, weather]
for file in files:
    file['Date'] = pd.to_datetime(file['Date'], format='%Y-%m-%d')
    file['Year'] = file['Date'].dt.year
    file['Month'] = file['Date'].dt.month
    file['Day'] = file['Date'].dt.day
    
# Visualize weather data
var = ['Tavg', 'DewPoint', 'PrecipTotal', 'StnPressure', 'Month', 'Station']
sns.pairplot(weather[var], hue='Station')
plt.savefig('../working/pairplot.png')

# Determine percentage of positive mosquitos per category
fig = plt.figure(figsize=(12,8))
groups = ['Year', 'Month', 'Species', 'Trap', 'Block']
cl.PercPos(fig, train, groups)
fig.tight_layout()
fig.show()
plt.savefig('../working/histograms.png')

### Data Processing
# Combined weather data by Station, then to train by Date
weather_stn1 = weather[weather['Station']==1]
weather_stn2 = weather[weather['Station']==2]
weather_stn1 = weather_stn1.drop('Station', axis=1)
weather_stn2 = weather_stn2.drop('Station', axis=1)
weather = weather_stn1.merge(weather_stn2, on='Date')

train = train.merge(weather, on='Date')
train = train.drop(['Date', 'Sunrise_y', 'Sunset_y', 'Depart_y', 'SnowFall_y', 'Depth_y', 'Year_y', 'Month_y', 'Day_y'], axis=1)
display(train.head())

# Convert categorical data into numerical
cat = ['Species', 'Street', 'Trap']
lbl = LabelEncoder()
for col in cat:
    lbl.fit(list(train[col].values))
    train[col] = lbl.transform(train[col].values)

# Identify features and labels
target_col = 'WnvPresent'
x_all = train.drop([target_col], axis=1)
y_all = train[target_col]
features = x_all.values
labels = y_all.values

# Model Application
names = ['GaussianNB', 'Decision Tree', 'Random Forest']
alg = [GaussianNB(), DecisionTreeClassifier(), RandomForestClassifier()]

cv = ShuffleSplit(features.shape[0], n_iter = 10, test_size = 0.2, random_state = 0)
scorer = make_scorer(roc_auc_score)

clf_dict = {}
for i in range(len(names)):
    clf_dict[names[i]] = alg[i]

for name, clf in clf_dict.iteritems():   
    score = cross_val_score(clf, features, labels, cv=cv, scoring=scorer)
    print '{} score: {:.2f}'.format(name, score.mean())

# Generate Learning Curve (Training size vs Score)
clf = GaussianNB()
cl.LearningCurve(clf, features, labels)
plt.savefig('../working/learning_curve_nb.png')
