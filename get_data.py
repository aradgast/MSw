import numpy as np
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
import time
# import threading
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import csv

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


# TODO need to check who to run in time period on a server
#  and how to send text if relevant

class Msw:
    def __init__(self, repeat_bool=False, wind_speed=None, wind_dirct=None, swell_dirct=None, swell_high=0.5,
                 swell_period=7, sunrise=6,
                 sunset=18):
        # try:
        #     self.marina_rating = self.to_dataframe(requests.api.get(
        #         'http://magicseaweed.com/api/d592918603bb8f15e84fcb8ba1a91b01/forecast/?spot_id=3979&fields=fadedRating'))
        #     self.tel_rating = self.to_dataframe(requests.api.get(
        #         'http://magicseaweed.com/api/d592918603bb8f15e84fcb8ba1a91b01/forecast/?spot_id=3978&fields=fadedRating'))
        #     if sum(np.array(self.marina_rating)) + sum(np.array(self.tel_rating)) <= 2:
        #         raise Exception('NoWaves')
        # except:
        #     raise Exception('NoWaves')

        self.url_marina = 'http://magicseaweed.com/api/d592918603bb8f15e84fcb8ba1a91b01/forecast/?spot_id=3979'
        self.url_tel_baroch = 'http://magicseaweed.com/api/d592918603bb8f15e84fcb8ba1a91b01/forecast/?spot_id=3978'
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

    def update(self):
        ''' this func will take new data from the api, and opreate the relavent funcs to init the alg'''
        self.df_marina = self.to_dataframe(requests.api.get(self.url_marina))
        self.df_tel_baroch = self.to_dataframe(requests.api.get(self.url_tel_baroch))
        self.get_days()
        self.email()

    def repeat(self):
        '''when init the repeat_bool field as True, calling this func will opreate the update func in interval time periods'''
        while self.repeat_bool:
            self.update()
            time.sleep(60 * 60 * 1)

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
            marina_swell_height = marina_data['swell'].iloc[i]['absMinBreakingHeight']  # [
            # 'components']['combined'][ 'height']
            marina_swell_period = marina_data['swell'].iloc[i]['components']['combined'][
                'period']
            tel_swell_height = tel_baroch_data['swell'].iloc[i]['absMinBreakingHeight']  # [
            # 'components']['combined']['height']
            tel_swell_period = tel_baroch_data['swell'].iloc[i]['components']['combined'][
                'period']
            avg_height = (marina_swell_height + tel_swell_height) / 2
            avg_period = (marina_swell_period + tel_swell_period) / 2
            if (avg_height >= self.swell_high and avg_period >= self.swell_period) or avg_period > 8:
                date = datetime.fromtimestamp(self.df_marina['localTimestamp'].iloc[i])
                if self.sunrise <= date.hour <= self.sunset:
                    if datetime.now().date() == date.date():
                        if datetime.now().hour <= date.hour:
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
        mask = self.swell_height_and_period() #calling the func to get the relvent days
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
        '''this method just organize the data to get a clear output'''
        good_days = self.df_tel_baroch.iloc[self.check_wind()]
        for i in range(len(good_days)):
            good_days['localTimestamp'].iloc[i] = datetime.fromtimestamp(good_days['localTimestamp'].iloc[i])
            # good_days['charts'].iloc[i] = good_days['charts'].iloc[i]['swell']
            good_days['condition'].iloc[i] = f"temp : {good_days['condition'].iloc[i]['temperature']} C "
            good_days['swell'].iloc[
                i] = f"height : {round(good_days['swell'].iloc[i]['components']['combined']['height'],2)} m , period : {good_days['swell'].iloc[i]['components']['combined']['period']} sec "
        # good_days = good_days.loc[:, ['localTimestamp', 'swell', 'condition', 'charts']]
        good_days = good_days.loc[:, ['localTimestamp', 'swell', 'condition']]
        # pd.DataFrame.to_csv(good_days, f"{datetime.now().date()} ({datetime.now().hour})", header=False,
        #                     index=False)  # todo
        self.good_days = good_days

    # TODO - add temp from condition and img
    # TODO - maybe image proccesing for better forcast
    def email(self):
        '''will send mail to the users in the csv file if relevent'''
        if not self.good_days.empty:
            with open("useres.csv") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row
                for name, email in reader:
                    subject = "Waves are here!!!"
                    body = f'Hi {name}, \n you should check it out: \n\n {self.good_days} \n\n\n this messege sent to ' \
                           f'you by python script '
                    sender_email = "aradon1@gmail.com"
                    receiver_email = email
                    password = "Python2020"
                    # password = input("gmail password: ")

                    message = MIMEMultipart()
                    message["From"] = 'Arad Gast'
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

    def add_new_email(self, name, email):
        '''add new user to the csv'''
        #TODO if name is already on the list
        file = open('useres.csv', 'a')
        writer = csv.writer(file)
        writer.writerow([name, email])
        file.close()


# f = open('useres.csv', 'a')
# w = csv.writer(f)
# w.writerow(['arad', 'gast'])



if __name__ == '__main__':
    print('***************************')
    a = Msw(repeat_bool=True)
    a.update()