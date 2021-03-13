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

MER_CAT = ["-", "1-", "2-", "3-", "4-", "5-", "1328-", "6-", "1328-79", "1027-", "7-", "8-", "1318-", "9-", "10-112", "10-929", "10-929", "10-"]

RAK_CAT = ["", "10001", "10005", "10003", "10009", "10007", "10007", "10004", "10013", "10008", "10006", "10014", "10011", "10010", "1125", "1126", "1510", "10002"]

MER_SOLD = ["", "status_trading_sold_out=1", "status_on_sale=1"]

RAK_SOLD = ["", "&transaction=soldout", "&transaction=selling"]

###########################
#      generate param     #
###########################

def mer_params(**kwargs):
    
    cat = int(kwargs.get("category"))
    sold = int(kwargs.get("sold"))
    
    cat_list = MER_CAT[cat].split("-")
    
    narrow = {
        "category_root": cat_list[0],
        "category_child": cat_list[1],
        "is_sold": MER_SOLD[sold],
    }
    
    return narrow
    
    
def rak_params(**kwargs):
    
    cat = int(kwargs.get("category"))
    sold = int(kwargs.get("sold"))
    
    narrow = {
        "category_id": RAK_CAT[cat],
        "transaction": RAK_SOLD[sold],
    }
    
    return narrow

###########################
#          func           #
###########################

def make_list_dict(lst_obj, link_str, name_str, price_str, sold, image):
    dict_ = {
        "href": link_str,
        "name": name_str,
        "price": price_str,
        "sold": sold,
        "image": image,
    }

    lst_obj.append(dict_)
    return lst_obj

def mer_scrape(url_):
    lst = []

    info = requests.get(url_, headers=SC_HEADERS)
    soup = BeautifulSoup(info.text, 'html.parser')

    # <section class="item-box"><a> を走査
    for item in soup.select("section > a", limit=50):

        link = item.get("href")
        link = str(link)
        name = item.find(class_="items-box-name").string
        price = item.find(class_="items-box-price").string
        
        image_fig = item.find(class_="items-box-photo")
        image = image_fig.find("img").get("data-src")

        sold = False
        if item.find(class_="item-sold-out-badge") is not None:
            sold = True

        merlink = MERCARI + link

        make_list_dict(lst, merlink, name, price, sold, image)

    #return json.dumps(lst, ensure_ascii=False)
    return lst

def rak_scrape(url_):
    lst = []

    info = requests.get(url_, headers=SC_HEADERS)
    soup = BeautifulSoup(info.text, 'html.parser')

    for item in soup.select(".item-box", limit=50):
        dict_ = {}
        
        p_ = item.select("p", class_=".item-box__item-name")[0]
        a_ = p_.select("a")[0]
        name = a_.select("span")[0].string
        link = a_.get("href")
        
        price_p = item.select("p", class_="item-box__item-price")[1]
        price = price_p.select("span")[1].string

        image_div = item.find(class_="item-box__image-wrapper")
        # image = image_div.find("img").get("src")
        image = image_div.find("meta").get("content")

        sold = False
        if item.find(class_="item-box__soldout_ribbon") is not None:
            sold = True
        
        make_list_dict(lst, link, name, price, sold, image)
    
    #return json.dumps(lst, ensure_ascii=False)
    return lst

def yahoo_scrape(url_):
    lst = []
    
    info = requests.get(url_, headers=SC_HEADERS)
    
    soup = BeautifulSoup(info.text, 'html.parser')
    
    for product in soup.select(".Product", limit=50):
        item = product.find(class_="Product__detail")

        det = item.select(".Product__titleLink")[0]
        link = det.get("href")
        name = det.string

        price_el = item.select(".Product__priceValue")[0]
        price = price_el.string

        image_el = product.find(class_="Product__image")
        image = image_el.find("img").get("src")

        sold = False
        
        make_list_dict(lst, link, name, price, sold, image)
        
    #return json.dumps(lst, ensure_ascii=False)
    return lst


###########################
#          route          #
###########################

# generate mercari list
@app.route('/mer/<keyword_>')
def mer_list(keyword_, **kwargs):
    keyword = urllib.parse.quote(keyword_)
    # spaceを+に変換
    keyword = keyword.replace('%20', '+')

    # narrow down dict
    narrow = mer_params(**kwargs)

    target_url = f'{MERCARI}/jp/search/?sort_order=&keyword={keyword}&category_root={narrow["category_root"]}&category_child={narrow["category_child"]}&brand_name=&brand_id=&size_group=&price_min=&price_max=&{narrow["is_sold"]}'

    lst = mer_scrape(target_url)

    return lst

# generate rakuma list
@app.route('/rak/<keyword_>')
def rakuma_list(keyword_, **kwargs):
    keyword = urllib.parse.quote(keyword_)
    
    # narrow down dict
    narrow = rak_params(**kwargs)
    
    target_url = f'{RAKUMA}/s?query={keyword}&category_id={narrow["category_id"]}{narrow["transaction"]}'
    
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
    narrowdown = body["narrowdown"]
    
    dict_ = {
        "mercari": mer_list(keyword, **narrowdown),
        "rakuma": rakuma_list(keyword, **narrowdown),
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
        run(app=app, host="localhost", port=7000, quiet=False, reloader=True)