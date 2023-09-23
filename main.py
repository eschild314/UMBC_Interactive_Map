import datetime as dt
import json
import urllib.request
#import sqlalchemy as db
import folium
from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Interval, Time
from sqlalchemy.orm import Mapped, mapped_column
# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

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
def foodTimes():
    foodTimeJson = urllib.request.urlopen("https://api.dineoncampus.com/v1/locations/status?site_id=5751fd3690975b60e04893e2&platform=0")
    openFoodLocations = {}
    for location in json.load(foodTimeJson)['locations']:
        openFoodLocations[location['name']] = location['status']['message']
        print(openFoodLocations[location['name']])
    return openFoodLocations

@app.route("/")
def umbc_map():
    min_longitude, max_longitude = -76.716805, -76.705468
    min_latitude, max_latitude = 39.251128, 39.260057
    openFoodLocations = foodTimes()
    print(openFoodLocations)
    m = folium.Map(
        location=[39.2554, -76.7107],
        zoom_start=17,
        zoom_control=False,
        control_scale=False,
        max_bounds=True,
        min_lat=min_latitude,
        max_lat=max_latitude,
        min_lon=min_longitude,
        max_lon=max_latitude,
    )
    if True:
        folium.Marker(
            location=[39.2551755,-76.7113790],
            popup="test",
        ).add_to(m)
    folium.CircleMarker([max_latitude, min_longitude], tooltip="Upper Left Corner").add_to(m)
    folium.CircleMarker([min_latitude, min_longitude], tooltip="Lower Left Corner").add_to(m)
    folium.CircleMarker([min_latitude, max_longitude], tooltip="Lower Right Corner").add_to(m)
    folium.CircleMarker([max_latitude, max_longitude], tooltip="Upper Right Corner").add_to(m)
    return m.get_root().render()

def iframe():
    """Embed a map as an iframe on a page."""
    m = umbc_map()

    # set the iframe width and height
    m.get_root().width = "800px"
    m.get_root().height = "600px"
    iframe = m.get_root()._repr_html_()

    return render_template_string(
        """
            <!DOCTYPE html>
            <html>
                <head></head>
                <body>
                    <h1>Using an iframe</h1>
                    {{ iframe|safe }}
                </body>
            </html>
        """,
        iframe=iframe,
    )

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run()
    delete_databases()
    make_databases()
    fillGenParking()
    with app.app_context():
        print(genParking.query.all())
    print(str(dt.date.today()))


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
