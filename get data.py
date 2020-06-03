import numpy as np
import json
import pandas_datareader as web
import requests
import pandas as pd
import matplotlib.pyplot as plt
from urllib.request import urlretrieve
from datetime import datetime


class Msw:
    def __init__(self):
        self.url_marina = requests.api.get(
            'http://magicseaweed.com/api/d592918603bb8f15e84fcb8ba1a91b01/forecast/?spot_id=3979')
        self.url_tel_baroch = requests.api.get(
            'http://magicseaweed.com/api/d592918603bb8f15e84fcb8ba1a91b01/forecast/?spot_id=3978')
        self.df_marina = self.to_dataframe(self.url_marina)
        self.df_tel_baroch = self.to_dataframe(self.url_tel_baroch)

    def to_dataframe(self, url):
        return pd.DataFrame((pd.read_json(url.text)))

    def swell_height_and_period(self):
        sampler_num = self.df_marina.shape[0]
        days_list = []
        good_days = 0
        for i in range(sampler_num):
            marina_swell_height = pd.DataFrame(self.df_marina['swell']).iloc[i]['swell']['components']['combined'][
                'height']
            marina_swell_period = pd.DataFrame(self.df_marina['swell']).iloc[i]['swell']['components']['combined'][
                'period']
            tel_swell_height = pd.DataFrame(self.df_tel_baroch['swell']).iloc[i]['swell']['components']['combined'][
                'height']
            tel_swell_period = pd.DataFrame(self.df_tel_baroch['swell']).iloc[i]['swell']['components']['combined'][
                'period']
            avg_height = (marina_swell_height + tel_swell_height) / 2
            avg_period = (marina_swell_period + tel_swell_period) / 2
            if avg_height > 0.5 and avg_period >= 6:
                date = datetime.fromtimestamp(self.df_marina['localTimestamp'].iloc[i])
                if 6 <= date.hour <= 18:
                    days_list.append(date)
                    good_days +=1

        return days_list
        # return (np.array(days_list).reshape((good_days,1)))

    def check_wind(self):
        pass

    def add_tmp_and_map(self):
        pass


if __name__ == '__main__':
    print('***************************')
    # print(ani_marina)
    # a = ani_marina.iloc[0].get('swell')
    # urlretrieve(a, "pic.png")
    # print(b.get('swell').get('components').get('combined').get('height'))
    # marina = marina.text
    # marina = pd.read_(url_marina.text)
    # marina = pd.DataFrame(marina)
    # a = pd.DataFrame(marina['swell'])
    # b = a.iloc[0]['swell']['components']['combined']['height']
    # c = b.get('absMinBreakingHeight')
    # b = a.iloc[1].get('absMinBreakingHeight')
    marina = Msw()
    a = marina.swell_height_and_period()
    for i in range(len(a)):
        print(a[i])
    # b = marina.df_marina.shape
    # print(b)
