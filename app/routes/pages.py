import requests
import math
from flask import Blueprint, render_template, request, current_app
import cloudinary
import cloudinary.uploader
from app.models import db, Memory
from flask import current_app
from flask import render_template, request, redirect, url_for

def cloudinary_upload(file_storage):
    # Cloudinary設定（毎回セットしても動くけど、簡単のため関数内）
    cloudinary.config(
        cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=current_app.config["CLOUDINARY_API_KEY"],
        api_secret=current_app.config["CLOUDINARY_API_SECRET"],
        secure=True
    )
    res = cloudinary.uploader.upload(file_storage, folder="playplanner")
    return res["secure_url"]

pages = Blueprint("pages", __name__)
def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl   = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return 2*R * math.asin(math.sqrt(a))

def rank_shops_rule_based(mid, shops, prefer_genres=None):
    prefer_genres = prefer_genres or []
    ranked = []
    for s in shops:
        d = haversine_m(mid["lat"], mid["lng"], s["lat"], s["lng"])
        score = -d
        if s["genre"] and any(g in s["genre"] for g in prefer_genres):
            score += 500
        ranked.append((score, d, s))
    ranked.sort(reverse=True, key=lambda x: x[0])

    out = []
    for score, d, s in ranked:
        s2 = dict(s)
        s2["distance_m"] = int(d)
        s2["score"] = round(score, 1)
        out.append(s2)
    return out

# --- geocode_station / search_hotpepper_shops など他の関数 ---
def geocode_station(name: str):
    ...

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
HOTPEPPER_GOURMET_URL = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

def geocode_station(name: str):
    params = {
        "address": f"{name}駅",
        "key": current_app.config["GOOGLE_MAPS_SERVER_KEY"],
        "language": "ja",
        "region": "jp",
    }
    r = requests.get(GEOCODE_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    if data["status"] != "OK":
        raise ValueError(data.get("error_message", "Geocode failed"))

    loc = data["results"][0]["geometry"]["location"]
    return {"name": name, "lat": loc["lat"], "lng": loc["lng"]}


def midpoint(points):
    lat = sum(p["lat"] for p in points) / len(points)
    lng = sum(p["lng"] for p in points) / len(points)
    return {"name": "中間地点", "lat": lat, "lng": lng}


@pages.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@pages.route("/map", methods=["GET", "POST"])
def show_map():
    # 1. ページを最初に開いたとき (リンクをクリックしたとき)
    if request.method == "GET":
        # 計算はせずに、ただ入力フォームを表示する
        return render_template("map.html", shops=None)

    # 2. 検索ボタンを押したとき (POSTされたとき)
    stations = request.form.get("stations", "")
    selected_genre = request.form.get("genre", "")
    stations = stations.replace("、", ",").replace(".",",")
    names = [s.strip() for s in stations.split(",") if s.strip()]

    if len(names) < 2:
        return "駅名を2つ以上入力してください", 400

    points = [geocode_station(n) for n in names]
    mid = midpoint(points)

    shops = search_hotpepper_shops(mid["lat"], mid["lng"], range_=3, count=30,genre=selected_genre)
    ranked_shops = rank_shops_rule_based(mid, shops, prefer_genres=[])

    return render_template(
        "map.html",
        api_key=current_app.config["GOOGLE_MAPS_BROWSER_KEY"],
        points=points,
        mid=mid,
        shops=ranked_shops[:10], 
    )

@pages.route("/memories")
def memories_list():
    items = Memory.query.order_by(Memory.created_at.desc()).all()
    return render_template("memories.html", items=items)


@pages.route("/memories/new", methods=["GET", "POST"])
def memories_new():
    # GETのときは、URLパラメータから緯度経度などを受け取って画面を表示するだけ
    if request.method == "GET":
        lat = request.args.get("lat")
        lng = request.args.get("lng")
        shop_name = request.args.get("shop_name")
        shop_url = request.args.get("shop_url")
        title = request.args.get("title", "")
        api_key = current_app.config.get("GOOGLE_MAPS_BROWSER_KEY") # これを追加
        return render_template("memory_new.html", lat=lat, lng=lng, shop_name=shop_name, shop_url=shop_url)

    # POSTのとき（保存ボタンが押されたとき）
    # 1. フォームから届いた生データをすべて変数に入れる（ここで変数を定義！）
    title = request.form.get("title", "").strip()
    note  = request.form.get("note", "").strip()
    date  = request.form.get("date", "").strip()
    lat_raw = request.form.get("lat") # ここで定義しています！
    lng_raw = request.form.get("lng") # ここで定義しています！
    shop_name = request.form.get("shop_name")
    shop_url  = request.form.get("shop_url")

    if not title:
        return "title が空です", 400

    # 2. 緯度(lat)の変換処理
    lat = None
    if lat_raw: # 値が存在するかチェック
        lat_str = str(lat_raw).strip() # 文字列にして余計な空白を消す
        if lat_str and lat_str != "None": # 空文字や"None"文字じゃないかチェック
            try:
                lat = float(lat_str)
            except ValueError:
                lat = None

    # 3. 経度(lng)の変換処理
    lng = None
    if lng_raw:
        lng_str = str(lng_raw).strip()
        if lng_str and lng_str != "None":
            try:
                lng = float(lng_str)
            except ValueError:
                lng = None

    # 画像のアップロード
    image = request.files.get("image")
    image_url = None
    if image and image.filename:
        image_url = cloudinary_upload(image)

    # 4. DB保存
    m = Memory(
        title=title,
        note=note,
        date=date,
        lat=lat,
        lng=lng,
        shop_name=shop_name,
        shop_url=shop_url,
        image_url=image_url
    )
    db.session.add(m)
    db.session.commit()

    # 完了したら一覧へ
    return redirect(url_for("pages.memories_list"))

def search_hotpepper_shops(lat, lng, range_=3, count=30, keyword=None,genre=""):
    """
    range_ : 1=300m, 2=500m, 3=1000m(初期値), 4=2000m, 5=3000m
    count  : 最大100まで
    """
    key = current_app.config.get("HOTPEPPER_API_KEY")
    if not key:
        raise ValueError("HOTPEPPER_API_KEY が .env にありません")

    params = {
        "key": key,
        "format": "json",
        "lat": lat,
        "lng": lng,
        "range": range_,
        "count": count,
        "genre":genre,
        "order": 4,      # おすすめ順（ただし位置検索は距離順になることがある） :contentReference[oaicite:1]{index=1}
        "type": "lite",  # 必要最低限に（速くなる）
    }
    if keyword:
        params["keyword"] = keyword

    r = requests.get(HOTPEPPER_GOURMET_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    results = data.get("results", {})
    shops = results.get("shop", [])
    if not shops:
        return []

    # アプリで使いやすい形に整形
    out = []
    for s in shops:
        out.append({
            "id": s.get("id"),
            "name": s.get("name"),
            "address": s.get("address"),
            "access": s.get("access"),
            "lat": float(s.get("lat")) if s.get("lat") else None,
            "lng": float(s.get("lng")) if s.get("lng") else None,
            "genre": (s.get("genre") or {}).get("name"),
            "budget": (s.get("budget") or {}).get("average"),
            "catch": s.get("catch"),
            "url": ((s.get("urls") or {}).get("pc")),
            "photo": (((s.get("photo") or {}).get("pc") or {}).get("m")),
        })
    return [x for x in out if x["lat"] is not None and x["lng"] is not None]


@pages.route("/memories/map")
def memories_all_map():
    # 1. ここで「items_raw」という名前でデータベースから取得します
    items_raw = Memory.query.all()
    
    # 2. 空のリストを準備
    items_to_send = []
    
    # 3. items_raw の中身を一つずつ取り出して辞書にする
    for m in items_raw:
        items_to_send.append({
            "id": m.id,
            "title": m.title,
            "date": m.date,
            "lat": m.lat,
            "lng": m.lng,
            "image_url": m.image_url,
            "shop_name": m.shop_name,
            "note":m.note
        })

    # 4. 変換した items_to_send をテンプレートに渡す
    return render_template(
        "memories_all_map.html",
        items=items_to_send,
        api_key=current_app.config["GOOGLE_MAPS_BROWSER_KEY"]
    )



@pages.route("/memories/<int:id>/delete", methods=["POST"])
def memories_delete(id):
    # IDを元に削除対象のデータを取得
    m = Memory.query.get_or_404(id)
    
    # データベースから削除
    db.session.delete(m)
    db.session.commit()
    
    # 一覧画面に戻る
    return redirect(url_for("pages.memories_list"))