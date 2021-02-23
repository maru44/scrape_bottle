import os
import requests, json, urllib
from bs4 import BeautifulSoup

""" bottle """
from bottle import Bottle, route, run, request

app = Bottle()

""" constant """
players = {
    "CR7": {"team": "Ubentus", "number": 7, "nation": "Portugees", "position": "FW"},
    "Messi": {"team": "FCBarcelona", "number": 10, "nation": "Argentina", "position": "FW"},
    "Ibra": {"team": "AC Milan", "number": 11, "nation": "Sweden", "position": "FW"}
}

SC_HEADERS = {
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "cross-site",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    #"Referrer": "https://www.mercari.com/",
}

# origins
MERCARI = "https://www.mercari.com"
RAKUMA = "https://fril.jp"

###########################
#          func           #
###########################

def make_list_dict(lst_obj, link_str, name_str, price_str):
    dict_ = {
        "href": link_str,
        "name": name_str,
        "price": price_str,
    }

    lst_obj.append(dict_)
    return lst_obj

def mer_scrape(url_):
    lst = []

    info = requests.get(url_, headers=SC_HEADERS)
    soup = BeautifulSoup(info.text, 'html.parser')

    for item in soup.select("section > a", limit=20):

        link = item.get("href")
        link = str(link)
        name = item.find(class_="items-box-name").string
        price = item.find(class_="items-box-price").string

        merlink = MERCARI + link

        make_list_dict(lst, merlink, name, price)

    #return json.dumps(lst, ensure_ascii=False)
    return lst

def rak_scrape(url_):
    lst = []

    info = requests.get(url_, headers=SC_HEADERS)
    soup = BeautifulSoup(info.text, 'html.parser')

    for item in soup.select(".item-box__text-wrapper", limit=20):
        dict_ = {}
        
        p_ = item.select("p", class_=".item-box__item-name")[0]
        a_ = p_.select("a")[0]
        name = a_.select("span")[0].string
        link = a_.get("href")
        
        price_p = item.select("p", class_="item-box__item-price")[1]
        price = price_p.select("span")[1].string
        
        make_list_dict(lst, link, name, price)
    
    #return json.dumps(lst, ensure_ascii=False)
    return lst

def yahoo_scrape(url_):
    lst = []
    
    info = requests.get(url_, headers=SC_HEADERS)
    
    soup = BeautifulSoup(info.text, 'html.parser')
    
    for item in soup.select(".Product__detail", limit=20):
        det = item.select(".Product__titleLink")[0]
        link = det.get("href")
        name = det.string
        price_el = item.select(".Product__priceValue")[0]
        price = price_el.string
        
        make_list_dict(lst, link, name, price)
        
    #return json.dumps(lst, ensure_ascii=False)
    return lst


###########################
#          route          #
###########################

# generate mercari list
@app.route('/mer/<keyword_>')
def mer_list(keyword_):
    keyword = urllib.parse.quote(keyword_)
    # spaceを+に変換
    keyword = keyword.replace('%20', '+')

    target_url = "".join([MERCARI, '/jp/search/', '?keyword=', keyword])

    lst = mer_scrape(target_url)
    return lst

# generate rakuma list
@app.route('/rak/<keyword_>')
def rakuma_list(keyword_):
    keyword = urllib.parse.quote(keyword_)
    target_url = "".join([RAKUMA, '/search/', keyword])
    
    lst = rak_scrape(target_url)
    return lst

# general yahoo list
@app.route('/yah/<keyword_>')
def yahoo_list(keyword_):
    keyword = urllib.parse.quote(keyword_)
    # spaceを+に変換
    keyword = keyword.replace("%20", "+")
    
    target_url = "https://auctions.yahoo.co.jp/search/search?aq=-1&auccat=&ei=utf-8&fr=auc_top&oq=&p={}&sc_i=&tab_ex=commerce".format(keyword)
    lst = yahoo_scrape(target_url)
    
    return lst

@app.route('/good')
def good():
    return json.dumps(players)

# test
@app.route('/test', method="POST")
def test():
    bod = json.load(request.body)
    ret = bod["keyword"] + "bbb"
    return ret

@app.route('/global', method="POST")
def glo():
    body = json.load(request.body)
    keyword = body["keyword"]
    
    dict_ = {
        "mercari": mer_list(keyword),
        "rakuma": rakuma_list(keyword),
        "yahoo": yahoo_list(keyword),
    }

    return dict_

@app.route('/')
def index():
    return json.dumps(players)

if __name__ == "__main__":
    if os.environ.get('LOCATION') == 'heroku':
        run(app=app, host="0.0.0.0", port=5000)
    else:
        run(app=app, host="localhost", port=8000, quiet=False, reloader=True)