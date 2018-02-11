# coding=utf-8

import csv
import numpy as np
import xgboost as xgb


def get_mean(cur_wind_list):
    # compute the merged data by calculating the mean without the smallest and largest items
    cur_wind_list.sort()  # sort the wind data
    k = len(cur_wind_list)
    sum, ave = 0.0, 16.0
    s, e = 2, k - 3
    for j in range(s, e + 1):
        sum += cur_wind_list[j]
    ave = sum / (e - s + 1)
    return ave


def merge_data():
    # load XGBoost model
    params = {'eta': 0.1, 'seed': 0, 'subsample': 0.8, 'colsample_bytree': 0.8, 'objective': 'reg:linear',
              'max_depth': 3, 'min_child_weight': 1}
    ml_xgb = xgb.Booster(params)
    ml_xgb.load_model('./xgboost.model')

    # merge data
    headers = ['xid', 'yid', 'date_id', 'hour', 'wind', 'rainfall']
    for date in range(6, 11):
        merge_file = open('../merge_data/MergeData{}.csv'.format(date), 'a+', newline='')
        print("=========================")
        print("open a new file, date: {}".format(date))
        print("=========================")
        merge_csv = csv.DictWriter(merge_file, fieldnames=headers)
        merge_csv.writeheader()
        with open('../split_data/ForecastData{}.csv'.format(date)) as f:
            prev_point = ('-1', '-1', '-1', '-1')
            cur_wind_list = []
            cur_rain_list = []
            f_csv = csv.DictReader(f)
            for row in f_csv:
                xid, yid, date_id, hour, model, wind, rainfall = row['xid'], row['yid'], row['date_id'], row['hour'], \
                                                                 row['model'], row['wind'], row['rainfall']
                if (xid, yid, date_id, hour) != prev_point:
                    if len(cur_wind_list) != 0:
                        if len(cur_wind_list) != 10 or len(cur_rain_list) != 10:
                            print("Error! (%s,%s,%s) has %d models" % (xid, yid, date_id, len(cur_wind_list)))
                        # compute the merged data
                        # if there exist a value in between [13.5, 16.5], we use ML model to merge
                        # wind
                        wind_median = np.median(cur_wind_list)
                        wind_ave = get_mean(cur_wind_list)
                        w_min, w_max = min(cur_wind_list), max(cur_wind_list)
                        if (13 <= w_min <= 16) or (13 <= w_max <= 16) or (13 <= wind_median <= 16):
                            xgdmat = xgb.DMatrix(cur_wind_list)
                            wind_xgb = ml_xgb.predict(xgdmat)[0]
                            merged_wind = wind_xgb
                        else:
                            merged_wind = 0.35 * wind_median + 0.65 * wind_ave
                        # rainfall
                        rain_median = np.median(cur_rain_list)
                        rain_ave = get_mean(cur_rain_list)
                        merged_rain = 0.35 * rain_median + 0.65 * rain_ave
                        # write merged data to new file
                        row['wind'] = merged_wind
                        row['rainfall'] = merged_rain
                        row['xid'], row['yid'] = prev_point[0], prev_point[1]
                        row['date_id'], row['hour'] = prev_point[2], prev_point[3]
                        row.pop('model')
                        merge_csv.writerow(row)
                        # then create new list for the next point
                        cur_wind_list = []
                        cur_rain_list = []
                    # update 'prev' point
                    prev_point = (xid, yid, date_id, hour)
                cur_wind_list.append(float(wind))
                cur_rain_list.append(float(rainfall))
            # remember to record the last 10 lines of data
            wind_median = np.median(cur_wind_list)
            wind_ave = get_mean(cur_wind_list)
            merged_wind = 0.35 * wind_median + 0.65 * wind_ave
            rain_median = np.median(cur_rain_list)
            rain_ave = get_mean(cur_rain_list)
            merged_rain = 0.35 * rain_median + 0.65 * rain_ave
            # write merged data to new file
            row = dict()
            row['wind'] = merged_wind
            row['rainfall'] = merged_rain
            row['xid'], row['yid'] = prev_point[0], prev_point[1]
            row['date_id'], row['hour'] = prev_point[2], prev_point[3]
            merge_csv.writerow(row)
        merge_file.close()


if __name__ == '__main__':
    merge_data()
