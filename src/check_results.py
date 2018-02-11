# coding=utf-8

import os

file_path = '../results_tmp/'
file_names = os.listdir(file_path)

total_min = 0
for file_name in file_names:
    print(file_name)
    with open(file_path+file_name, 'r') as f:
        for line in f:
            total_min += 2
            # xid, yid, hour, min = line.split(',')
print("number of paths: %d" % len(file_names))
# print("total min: %d" % total_min)
print("maybe min: %d" % (24*60*(50-len(file_names)) + total_min))
