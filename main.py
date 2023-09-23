import datetime as dt
import json
import urllib.request
#import sqlalchemy as db
from flask import Flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Interval, Time
from sqlalchemy.orm import Mapped, mapped_column
# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.
def delete_databases():
    with app.app_context():
        db.drop_all()
def make_databases():
    with app.app_context():
        db.create_all()
db = SQLAlchemy()
# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///main.db"
# initialize the app with the extension
db.init_app(app)
class genParking(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[int] = mapped_column(String, nullable=False)
    start: Mapped[Time] = mapped_column(Time, nullable=False)
    end: Mapped[Time] = mapped_column(Time, nullable=False)
#genParkingTimes=[[0,datetime.time()]]
def retrieve_closed_dates():
    print("test")
def fillGenParking():
    for count in range(7):
        parking = genParking(
            day=count,
            start=dt.time(7,0,0),
            end=dt.time(16,0,0)
        )
        with app.app_context():
            db.session.add(parking)
            db.session.commit()
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    delete_databases()
    make_databases()
    fillGenParking()
    with app.app_context():
        print(genParking.query.all())
    openFoodLocations = {}
    #foodTimeJson = urllib.request.urlopen("https://api.dineoncampus.com/v1/locations/status?site_id=5751fd3690975b60e04893e2&platform=0")
    print(str(dt.date.today()))
    #for location in json.load(foodTimeJson)['locations']:
        #openFoodLocations[location['name']] = location['status']['message']
        #print(openFoodLocations[location['name']])
    print(openFoodLocations)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/