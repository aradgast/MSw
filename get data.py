import numpy as np
import json
import pandas_datareader as web
import requests
import pandas as pd
import matplotlib.image as img
import matplotlib.pyplot as plt
from urllib.request import urlretrieve
from datetime import datetime
from scipy import misc
from PIL import Image
from io import BytesIO


# TODO need to check who to run in time period on a server
#  and how to send text if relevant

class Msw:
    def __init__(self, wind_speed=None, wind_dirct=None, swell_dirct=None, swell_high=0.6, swell_period=7, sunrise=6,
                 sunset=18):
        self.url_marina = requests.api.get(
            'http://magicseaweed.com/api/d592918603bb8f15e84fcb8ba1a91b01/forecast/?spot_id=3979')
        self.url_tel_baroch = requests.api.get(
            'http://magicseaweed.com/api/d592918603bb8f15e84fcb8ba1a91b01/forecast/?spot_id=3978')
        self.df_marina = self.to_dataframe(self.url_marina)
        self.df_tel_baroch = self.to_dataframe(self.url_tel_baroch)
        self.high_days = None
        self.wind_speed = wind_speed
        self.wind_dirct = wind_dirct
        self.swell_higt = swell_high
        self.swell_period = swell_period
        self.swell_dirct = swell_dirct
        self.sunrise = sunrise
        self.sunset = sunset

    def to_dataframe(self, url):
        return pd.DataFrame((pd.read_json(url.text)))

    def swell_height_and_period(self):  # TODO need to change to avg. min/max breaking height
        # TODO check the good dirct for tel_barch and mraina swell
        sampler_num = self.df_marina.shape[0]
        days_list = []
        index_list = []
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
            if avg_height > self.swell_higt and avg_period >= self.swell_period:
                date = datetime.fromtimestamp(self.df_marina['localTimestamp'].iloc[i])
                if self.sunrise <= date.hour <= self.sunset:
                    days_list.append(date)
                    index_list.append(i)
                    good_days += 1
        self.high_days = days_list
        return index_list
        # return (np.array(days_list).reshape((good_days,1)))

    def check_wind(self):
        index_list = self.swell_height_and_period()
        for i in enumerate(index_list):
            pass

    #     TODO - on_shor - if period>=9 so top 25 kp/h if period <9 so wind 20 kp/h
    #     TODO - cross_shor - same as on_shor, check the better dirct
    #     TODO - off_shor - height

    def add_tmp_and_map(self):
        pass
    # TODO - add temp from condition and img
    # TODO - maby image proccesing for better forcast


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
    # marina = Msw()

    # a = marina.swell_height_and_period()
    # b = marina.df_marina.shape
    # print(b)
    # print(marina.high_days)
    # a = Msw()
    # url = (pd.DataFrame(a.df_marina['charts']).iloc[0][0])
    # url = url.get('swell')
    # response = requests.get(url)
    # img = Image.open(BytesIO(response.content)).convert("L")
    # plt.imshow(img, cmap="gray")
    # plt.show()
    # mat = np.array(img)
    # print(mat.shape)