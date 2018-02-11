# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os

folder = 'results_tmp/'


def file_name(dir):
    for root, dirs, files in os.walk(dir):
        return files


def time(t):
    t = str(t)
    if len(t) == 1:
        return str('0' + t)
    return t


dir = os.path.dirname(os.path.realpath(__file__))
dir += '/' + folder
files = file_name(dir)
result = pd.DataFrame()
for file in files:
    print(file)
    date, city = file[:-4].split('_')
    data = pd.DataFrame()
    file = folder + '/' + file
    df = pd.read_csv(file, header=None)
    a = np.array(df.iloc[:, 2:3]).ravel()
    b = np.array(df.iloc[:, 3:4]).ravel()
    l = []
    for i in range(len(a)):
        l.append(time(a[i]) + ':' + time(b[i]))
    t = pd.Series(l, name='time')
    city = pd.Series([city for _ in range(len(a))], name='city')
    date = pd.Series([date for _ in range(len(a))], name='date')
    data = pd.concat([city, date, t, data, df.iloc[:, 0:2]], axis=1)
    #    data = pd.concat([data,t],axis=1)
    #    data = pd.concat([data,df.iloc[:,0:2]],axis=1)
    result = result.append(data, ignore_index=True)

print(result.size)
result.to_csv('result.csv', header=None, index=None)
