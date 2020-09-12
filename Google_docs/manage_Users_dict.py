from Google_docs import fetch_data
import json

class Contacts:
    def __init__(self, dict, df):
        self.dict = dict
        self.df = df

    def update(self):
        for row in self.df.iloc:
            self.dict[row.loc['Name']] = row.loc['Email'], row.loc['Phone number']
        self.save()

    def save(self):
        json.dump(self.dict, open("myfile.json", 'w'))


if __name__ == '__main__':
    a = Contacts(json.load(open('myfile.json')), fetch_data.main())
    a.update()

