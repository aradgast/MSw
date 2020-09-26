import requests
import pandas as pd
#if i will want to extend the users
bot_token = '1393856489:AAFdXkyWqrivY8PVKF9AC8modSJMY0G_IQo'
get_update = f'https://api.telegram.org/bot{bot_token}/getUpdates'

response = requests.get(get_update)
update = pd.DataFrame((pd.read_json(response.text)))
# print(len(update))
# update = update['result'][0]
# update = update['message']
# update = update['text']
# print(update['from']['id'])

import dict_contact
contacts = {}
for i in range(len(update)):
    if update['result'][i]['message']['text'] == '/sign_in':
        contacts[update['result'][i]['message']['from']['first_name']] = update['result'][i]['message']['from']['id']
print(contacts)


