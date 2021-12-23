# import Google_docs
# from Google_docs import manage_Users_dict, fetch_data
# import numpy as np
# import json
# import pandas_datareader as web
# import matplotlib.image as img
# import matplotlib.pyplot as plt
# from urllib.request import urlretrieve
# for expend the info sown in the tables
# from scipy import misc
# from PIL import Image
# from io import BytesIO
import time
# import threading
# import smtplib, ssl
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# import csv
import keys
import users
import requests
import pandas as pd
from datetime import datetime
import pytz

# for debugging
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


class Msw:
    def __init__(self, repeat_bool=False, wind_speed=None, wind_dirct=None, swell_dirct=None, swell_high=0.6,
                 swell_period=7, sunrise=6,
                 sunset=18):

        self.url_marina = f'http://magicseaweed.com/api/{keys.msw_key}/forecast/?spot_id=3979&units=eu'
        self.url_tel_baroch = f'http://magicseaweed.com/api/{keys.msw_key}/forecast/?spot_id=3978&units=eu'
        self.df_marina = None
        self.df_tel_baroch = None
        self.wind_speed = wind_speed
        self.wind_direct = wind_dirct
        self.swell_high = swell_high
        self.swell_period = swell_period
        self.swell_direct = swell_dirct
        self.sunrise = sunrise
        self.sunset = sunset
        self.good_days = pd.DataFrame()
        self.repeat_bool = repeat_bool
        self.local_israel_tz = pytz.timezone('Israel')
        self.on_shore_flag = False

    def update(self):
        ''' this func will take new data from the api, and opreate the relavent funcs to init the algo'''
        self.df_marina = self.to_dataframe(requests.api.get(self.url_marina))
        self.df_tel_baroch = self.to_dataframe(requests.api.get(self.url_tel_baroch))
        self.get_days()
        if not self.good_days.empty:
            self.telegram_bot_sendtext()

    def repeat(self):
        '''when init the repeat_bool field as True, calling this func will opreate the update func in interval time periods'''
        while self.repeat_bool:
            self.update()
            time.sleep(60 * 60 * 10)  # 10 hours pause

    def to_dataframe(self, url):
        return pd.DataFrame((pd.read_json(url.text)))

    def swell_height_and_period(self):
        # TODO need to change to avg. min/max breaking height
        # TODO check the good dirct for tel_barch and mraina swell
        sampler_num = self.df_marina.shape[0]
        days_list = []
        index_list = []
        good_days = 0
        marina_data = self.df_marina
        tel_baroch_data = self.df_tel_baroch
        for i in range(sampler_num):
            marina_swell_height_min = marina_data['swell'].iloc[i]['absMinBreakingHeight']
            marina_swell_height_max = marina_data['swell'].iloc[i]['absMaxBreakingHeight']
            marina_swell_period = marina_data['swell'].iloc[i]['components']['combined']['period']
            tel_swell_height_min = tel_baroch_data['swell'].iloc[i]['absMinBreakingHeight']
            tel_swell_height_max = tel_baroch_data['swell'].iloc[i]['absMaxBreakingHeight']
            tel_swell_period = tel_baroch_data['swell'].iloc[i]['components']['combined']['period']
            avg_height = (
                                 marina_swell_height_min + marina_swell_height_max + tel_swell_height_min
                                 + tel_swell_height_max) / 4
            avg_period = (marina_swell_period + tel_swell_period) / 2
            if (avg_height >= self.swell_high and avg_period >= self.swell_period) or avg_period > 8:
                date = datetime.fromtimestamp(self.df_marina['localTimestamp'].iloc[i])
                if self.sunrise <= date.hour <= self.sunset:
                    if datetime.now(self.local_israel_tz).date() == date.date():
                        if datetime.now(self.local_israel_tz).hour <= date.hour:
                            days_list.append(date)
                            index_list.append(i)
                            good_days += 1
                    else:
                        days_list.append(date)
                        index_list.append(i)
                        good_days += 1
        return index_list
        # return (np.array(days_list).reshape((good_days,1)))

    def check_wind(self):
        mask = self.swell_height_and_period()  # calling the func to get the relvent days
        relavent_days_marina = self.df_marina.iloc[mask]
        relavent_days_tel = self.df_marina.iloc[mask]
        no_wind_days = []
        for i in range(len(mask)):
            if 45 < relavent_days_tel.iloc[i][6]['direction'] < 135 and 45 < relavent_days_marina.iloc[i][6]['direction']\
                    < 135:
                no_wind_days.append(mask[i])
                self.on_shore_flag = True
            elif relavent_days_tel.iloc[i][6]['speed'] + relavent_days_marina.iloc[i][6]['speed'] < 40:
                no_wind_days.append(mask[i])
        return no_wind_days

    def get_days(self):
        """this method just organize the data to get a clear output"""
        good_days = self.df_tel_baroch.iloc[self.check_wind()]
        for i in range(len(good_days)):
            good_days['localTimestamp'].iloc[i] = datetime.fromtimestamp(good_days['localTimestamp'].iloc[i]) \
                                                      .strftime("%D %H:%M"), \
                                                  datetime.fromtimestamp(good_days['localTimestamp'].iloc[i]).strftime(
                                                      '%A')
            good_days['condition'].iloc[i] = f",temp : {good_days['condition'].iloc[i]['temperature']} C"
            good_days['swell'].iloc[
                i] = f"height : {round(good_days['swell'].iloc[i]['components']['combined']['height'], 2)}" \
                     f" m , period :{good_days['swell'].iloc[i]['components']['combined']['period']} sec"
        good_days = good_days.loc[:, ['localTimestamp', 'swell', 'condition']]

        self.good_days = good_days

    def telegram_bot_sendtext(self):

        messege_df = self.good_days.loc[:, ['localTimestamp', 'swell']]
        messege_df.set_index('localTimestamp', inplace=True)
        messege_df = messege_df.rename(columns={'localTimestamp': '', 'swell': ''})
        messege_df = messege_df.rename_axis(None)
        on_shore = ""
        if self.on_shore_flag:
            on_shore = "it's on shore, mate!"

        for key, value in users.bot_chatID.items():
            send_text = f'https://api.telegram.org/bot{keys.bot_token}/sendMessage?chat_id={value[0]}&parse_mode=Markdown' \
                        f'&text=Hi {key}, \nGO SURF! \n{on_shore}\n{messege_df} \n\n{value[1]}'
            #             f'test time {datetime.now(self.local_israel_tz).strftime("%H:%M")} '
            response = requests.get(send_text)

            # for testing before deploy
            # print(f'Hi {key}, \nGO SURF! {on_shore} \n{messege_df} \n\n{value[1]} ')


if __name__ == '__main__':
    print('***************************')
    a = Msw(repeat_bool=True)
    # a.repeat()
    a.update()
    print('done!')
