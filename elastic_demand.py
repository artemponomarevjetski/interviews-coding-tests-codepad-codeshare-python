#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 18:13:21 2020

@author: artemponomarev
"""

from __future__ import print_function
from statsmodels.compat import lzip
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import ols

beef = pd.read_csv('beef.csv')
print(beef)
beef_model = ols("Quantity ~ Price", data=beef).fit()
print(beef_model.summary())
fig = plt.figure(figsize=(12,8))
fig = sm.graphics.plot_partregress_grid(beef_model, fig=fig)
fig = plt.figure(figsize=(12, 8))
fig = sm.graphics.plot_ccpr_grid(beef_model, fig=fig)
fig = plt.figure(figsize=(12,8))
fig = sm.graphics.plot_regress_exog(beef_model, 'Price', fig=fig)
beef['Year'] = pd.to_datetime(beef['Year'], format="%Y")
beef['Date'] = beef.apply(lambda x:(x['Year'] + pd.tseries.offsets.BQuarterBegin(x['Quarter'])), axis=1)
beef.drop(['Year', 'Quarter'], axis=1, inplace=True)
beef.set_index('Date', inplace=True)
print(beef)
endog = beef['Quantity']
exog = sm.add_constant(beef['Price'])
mod = sm.RecursiveLS(endog, exog)
res = mod.fit()
print(res.summary())
res.plot_recursive_coefficient(range(mod.k_exog), alpha=None, figsize=(10,6))
fig = res.plot_cusum(figsize=(10,6))