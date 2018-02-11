# coding=utf-8

import csv
import time


def split_data():
    start_time = time.clock()  # This operation takes about 1850s

    pre_date = '-1'
    sub_file = None
    headers = ['xid', 'yid', 'date_id', 'hour', 'model', 'wind', 'rainfall']
    with open('../data/ForecastDataforTesting_201802.csv') as f:
        f_csv = csv.DictReader(f)
        sub_csv = None
        for row in f_csv:
            xid, yid, date_id, hour, model, wind, rainfall = row['xid'], row['yid'], row['date_id'], row['hour'], row[
                'model'], row['wind'], row['rainfall']
            if date_id != pre_date:
                pre_date = date_id
                if sub_file is not None:
                    sub_file.close()
                sub_file = open('../split_data/ForecastData%d.csv' % int(date_id), 'a+', newline='')
                print("open a new file, date %d" % int(date_id))
                sub_csv = csv.DictWriter(sub_file, headers)
                sub_csv.writeheader()
            sub_csv.writerow(row)
        sub_file.close()

    elapsed = time.clock() - start_time
    print("Elapsed time: %d seconds" % elapsed)


if __name__ == '__main__':
    # pass
    split_data()
