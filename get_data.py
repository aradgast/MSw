# import numpy as np
# import json
# import pandas_datareader as web
import requests
import pandas as pd
# import matplotlib.image as img
# import matplotlib.pyplot as plt
# from urllib.request import urlretrieve
from datetime import datetime
# from scipy import misc
# from PIL import Image
# from io import BytesIO
# import time
# import threading
# import smtplib, ssl
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# import csv
import pytz

# import Google_docs
# from Google_docs import manage_Users_dict, fetch_data

# for expend the info sown in the tables
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


class Msw:
    def __init__(self, repeat_bool=False, wind_speed=None, wind_dirct=None, swell_dirct=None, swell_high=0.6,
                 swell_period=7, sunrise=6,
                 sunset=18):

        self.url_marina = 'http://magicseaweed.com/api/d592918603bb8f15e84fcb8ba1a91b01/forecast/?spot_id=3979&units=eu'
        self.url_tel_baroch = 'http://magicseaweed.com/api/d592918603bb8f15e84fcb8ba1a91b01/forecast/?spot_id=3978&units=eu'
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

    def update(self):
        ''' this func will take new data from the api, and opreate the relavent funcs to init the algo'''
        self.df_marina = self.to_dataframe(requests.api.get(self.url_marina))
        self.df_tel_baroch = self.to_dataframe(requests.api.get(self.url_tel_baroch))
        self.get_days()
        if not self.good_days.empty:
            # self.email()
            self.telegram_bot_sendtext()

    def repeat(self):
        '''when init the repeat_bool field as True, calling this func will opreate the update func in interval time periods'''
        while self.repeat_bool:
            self.update()
            time.sleep(60 * 60 * 10)  # 10 hours pause

    def to_dataframe(self, url):
        return pd.DataFrame((pd.read_json(url.text)))

    def swell_height_and_period(self):  # TODO need to change to avg. min/max breaking height
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
            if relavent_days_tel.iloc[i][6]['speed'] + relavent_days_marina.iloc[i][6]['speed'] < 40:
                no_wind_days.append(mask[i])
            elif 45 < relavent_days_tel.iloc[i][6]['direction'] < 135 and 45 < relavent_days_marina.iloc[i][6][
                'direction'] < 135:
                no_wind_days.append(mask[i])
        return no_wind_days

    #     TODO - on_shor - if period>=9 so top 25 kp/h if period <9 so wind 20 kp/h
    #     TODO - cross_shor - same as on_shor, check the better dirct
    #     TODO - off_shor - height

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

    # TODO - add temp from condition and img

    def email(self):
        '''will send mail to the users in the csv file if relevent'''
        file_path = 'Google_docs\myfile.json'
        df_email = self.good_days.rename(columns={'localTimestamp': '', 'swell': '', 'condition': ''})
        df_email.reset_index(drop=True, inplace=True)
        if not self.good_days.empty:
            dict = json.load(open(file_path))
            for name in dict:
                subject = "Waves are here!!!"
                body = f'Hi {name}, \nyou should check it out: \n {df_email} \n\n\n this messege sent to ' \
                       f'you by python script, if you want to unsubscribe send mail to aradon1@gmail.com '
                sender_email = "aradon1@gmail.com"
                receiver_email = dict[name]
                password = input("gmail password: ")

                message = MIMEMultipart()
                message["From"] = "Wave's Alert"
                message["To"] = receiver_email
                message["Subject"] = subject
                message["Body"] = body
                message.attach(MIMEText(body, "plain"))
                text = message.as_string()

                port = 465
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                    server.login(sender_email, password)
                    server.sendmail(sender_email, receiver_email, text)

    def telegram_bot_sendtext(self):

        messege_df = self.good_days.loc[:, ['localTimestamp', 'swell']]
        messege_df.set_index('localTimestamp', inplace=True)
        messege_df = messege_df.rename(columns={'localTimestamp': '', 'swell': ''})
        messege_df = messege_df.rename_axis(None)

        bot_token = '1393856489:AAGYxtFgalnk1dg6VQ9iSi2VYpMW1Gzf1Yk'
        bot_chatID = {'Arad': ['787115422', 'Full Report \nhttps://magicseaweed.com/Hazuk-Beach-Surf-Report/3659/ \n\n'
                                            'Dromi surf cam \nhttps://beachcam.co.il/dromi2.html']}
                      # 'Omer': ['989958958', 'Full Report \nhttps://magicseaweed.com/Ashdod-Surf-Report/4219/ \n\n'
                      #                       'Gil surf cam \nhttps://www.youtube.com/watch?v=iRfU0NCVJnY'],
                      # 'Pita': ['1902388307', 'Full Report \nhttps://magicseaweed.com/Hilton-Surf-Report/3658/ \n\n'
                      #                        'Hilton surf cam \nhttps://beachcam.co.il/yamit.html'],
                      # 'Ofek': ['1204562422', 'Full Report \nhttps://magicseaweed.com/Backdoor-Haifa-Surf-Report/3987/'],
                      # 'Ofir': ['1203264499', 'Full Report \nhttps://magicseaweed.com/Ashdod-Surf-Report/4219/ \n\n'
                      #                        'Gil surf cam \nhttps://www.youtube.com/watch?v=iRfU0NCVJnY']}
        for key, value in bot_chatID.items():
            send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={value[0]}&parse_mode=Markdown' \
                        f'&text=Hi {key}, \nGO SURF! \n{messege_df} \n\n{value[1]} test '
            response = requests.get(send_text)
            # print(f'Hi {key}, \nGO SURF! \n{messege_df} \n\n{value[1]} ')


if __name__ == '__main__':
    print('***************************')
    a = Msw(repeat_bool=True)
    # a.repeat()
    a.update()
    # telegram_token = '1393856489:AAFdXkyWqrivY8PVKF9AC8modSJMY0G_IQo'
    # chat_id = '1393856489'
    # print(datetime.today().strftime('%A'))
