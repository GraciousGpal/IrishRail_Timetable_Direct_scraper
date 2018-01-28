# Import Core Modules
import re, sys, os, os.path, json
from setuptools.command.easy_install import main as install
import difflib


def moduleinstall(name):
        install([name])
        print("Restarting Process!.")
        os.execl(sys.executable, sys.executable, *sys.argv)


# Import Installed Packages
try:
    import httplib2
    from bs4 import BeautifulSoup
    from prettytable import PrettyTable
    import xml.etree.ElementTree
    import urllib.request
except ModuleNotFoundError as e:
    moduleinstall(re.search("'(.*)'", str(e)).group(1))

###### GETTING STATION CODES
if not (os.path.isfile("stationcodes.json")):
    url = "http://api.irishrail.ie/realtime/realtime.asmx/getAllStationsXML"
    print("Station Codes Not Found!\n Downloading.....")
    urllib.request.urlretrieve(url, 'getAllStationsXML.xml')  
    e = xml.etree.ElementTree.parse('getAllStationsXML.xml').getroot()
    stationcodes = {}
    objects = e.findall('{http://api.irishrail.ie/realtime/}objStation')
    for x in objects:
        stationcodes[x[0].text.lower()] =x[4].text
    with open('stationcodes.json', 'w') as outfile:
        json.dump(stationcodes, outfile, indent=4)
    os.remove("getAllStationsXML.xml")
    print("getAllStationsXML.xml Removed!")
######




dicts = {}
http = httplib2.Http()

stationcodes = json.load(open('stationcodes.json'))
os.remove("stationcodes.json")
class Irishrail_Parser:
    def __init__(self, code):
        self.version = "2.0"
        self.code = difflib.get_close_matches(code.lower(), [name for name in stationcodes])
        if len(self.code) != 0:
            self.code = difflib.get_close_matches(code.lower(), [name for name in stationcodes])[0]
        else:
            print("CODE Not Found -SETTING DEFAULT [Maynooth]")
            self.code = "maynooth"
        self.headers = {'Cookie':"key_station='{}'".format(self.code)}
        sys.stdout.write("Getting Data from Irish Rail [{} :{}]".format(str(self.code), str(stationcodes[self.code])))
        for x in range(0, 5):
            sys.stdout.write('.')
            sys.stdout.flush()
        try:
            cde = stationcodes[self.code]
        except KeyError:
            print("CODE Not Found -SETTING DEFAULT [Maynooth]")
            cde = "MYNTH"
        self.content = http.request("http://www.irishrail.ie/timetables/live-departure-times?code={}".format(cde), 'GET', headers=self.headers)
        sys.stdout.write('[Data Acquired]\n')
        self.soup = BeautifulSoup(str(self.content), "lxml")

    def gettimetable(self):
        northbound = getnorthbound(self.soup)
        northbounds = northbound[:]
        southbound = getsouthbound(self.soup, len(northbounds))
        # FORMAT  "Destination   "Origin"  "Sch" "ETA" "Due in"  Latest Information"
        dicts["northbound"] = northbound
        dicts["southbound"] = southbound
        if len(dicts["northbound"]) is 0 and len(dicts["southbound"]) is 0 :
            return "No updates avaliable at this time!."
        else:
            return dicts

    def __str__(self):
        table = self.gettimetable()
        if isinstance(table, str):
            return "No updates avaliable at this time!."
        else:
            x = PrettyTable()
            x.field_names = ["Destination", "Origin", "Sch", "ETA", "Due in", "Latest Information"]
            for list1s in table["northbound"]:
                x.add_row(list1s)
            y = PrettyTable()
            y.field_names = ["Destination", "Origin", "Sch", "ETA", "Due in", "Latest Information"]
            for lists in table["southbound"]:
                    y.add_row(lists)
            return str("[NORTH] bound \n{} \n [SOUTH] bound\n{}".format(x, y))


def getnorthbound(soup):
    data =[]
    rows =[]
    for item in soup.find_all('div', class_="panel-livedepartures"):
        # print(item.prettify())
        table = item
        table_body = table.find('tbody')
        if table_body is None:
            table_body = []
        else:
            rows = table_body.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip().replace("\\r", "").replace("\\n", "").replace("\\t", "") for ele in cols]
            data.append([ele for ele in cols]) # Get rid of empty values # data.append([ele for ele in cols if ele])
    northlist = []
    for item in data:
        if len(item) >= 5 and len(item) <= 6:
            northlist.append(item)
    #print("NORTHLIST : {}".format(northlist))
    return northlist


def getsouthbound(soup, datas=None):
    data = []
    for item2 in soup.find_all('div', class_="panel-livedepartures"):
        # print(item.prettify())
        table = item2
        table_body1 = table.find_all('tbody')
        for tables in table_body1:
            rows = tables.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip().replace("\\r", "").replace("\\n", "").replace("\\t", "") for ele in cols]
                data.append([ele for ele in cols]) # Get rid of empty values # data.append([ele for ele in cols if ele])
    southlist = []
    for item in data:
        # print(item, len(item))
        if len(item) >= 5 and len(item) <= 6:
            southlist.append(item)
    try:
        del southlist[:datas]
    except IndexError:
        return []
    return southlist


if __name__ == "__main__":
    while True:
        print("#############[IRISH RAIL TIME TABLE]#############")
        variable = input("Enter Station Name :")
        print(Irishrail_Parser(variable))
        reset = input("Press any key to continue .")