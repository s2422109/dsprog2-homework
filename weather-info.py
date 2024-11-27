import requests
import flet as ft

# 地域情報のURL
AREA_URL_TEMPLATE = "http://www.jma.go.jp/bosai/forecast/data/forecast/{region_id}.json"
AREA_JSON_URL = "http://www.jma.go.jp/bosai/common/const/area.json"

# JSONデータを取得する関数
def fetch_weather_data(region_id):
    url = AREA_URL_TEMPLATE.format(region_id=region_id)
    print(f"[INFO] 天気データを取得中: {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"[SUCCESS] 天気データ取得成功")
            return response.json()
        else:
            print(f"[ERROR] 天気データ取得失敗: ステータスコード {response.status_code}")
            return None
    except Exception as e:
        print(f"[EXCEPTION] 天気データ取得中にエラー発生: {e}")
        return None

# 地域IDと関連するオフィスを取得する関数
def fetch_region_data():
    print(f"[INFO] 地域IDを取得中: {AREA_JSON_URL}")
    try:
        response = requests.get(AREA_JSON_URL)
        if response.status_code == 200:
            print(f"[SUCCESS] 地域ID取得成功")
            return response.json()
        else:
            print(f"[ERROR] 地域ID取得失敗: ステータスコード {response.status_code}")
            return None
    except Exception as e:
        print(f"[EXCEPTION] 地域ID取得中にエラー発生: {e}")
        return None

# GUIアプリケーションを構築
def main(page: ft.Page):
    page.title = "地域別天気データ"
    page.scroll = ft.ScrollMode.AUTO

    # 地域IDを取得
    region_data = fetch_region_data()
    if not region_data:
        page.add(ft.Text("地域データの取得に失敗しました。"))
        return

    # class10s IDのリストを取得
    class10_ids = region_data.get("offices", {}).keys()

    # 天気情報を辞書に保存
    weather_info_dict = {}

    # 各地域の天気データを取得し辞書に保存
    for region_id in class10_ids:
        weather_data = fetch_weather_data(region_id)
        if weather_data:
            # weather_dataがリストの場合、最初の要素を処理する
            if isinstance(weather_data, list):
                weather_data = weather_data[0]  # 最初の要素を取り出す

            publishing_office = weather_data.get("publishingOffice", "不明")
            report_datetime = weather_data.get("reportDatetime", "不明")
            time_series = weather_data.get("timeSeries", [])

            if not time_series:
                continue  # timeSeriesがない場合はスキップ

            # 各timeSeries内の情報を辞書に格納
            for series_index, series in enumerate(time_series):
                time_defines = series.get("timeDefines", [])
                areas = series.get("areas", [])

                for area in areas:
                    area_name = area.get("area", {}).get("name", "不明")
                    area_code = area.get("area", {}).get("code", "不明")

                    weather_codes = area.get("weatherCodes", [])
                    weathers = area.get("weathers", [])
                    winds = area.get("winds", [])
                    waves = area.get("waves", [])
                    pops = area.get("pops", [])
                    reliabilities = area.get("reliabilities", [])
                    temps = area.get("temps", [])

                    for idx, time_define in enumerate(time_defines):
                        # 日時情報を辞書に格納
                        weather_info_dict[f"{region_id}_{area_name}_{time_define}"] = {
                            "発表局": publishing_office,
                            "発表日時": report_datetime,
                            "エリア": area_name,
                            "日時": time_define,
                            "天気コード": weather_codes[idx] if idx < len(weather_codes) else "情報なし",
                            "天気": weathers[idx] if idx < len(weathers) else "情報なし",
                            "風": winds[idx] if idx < len(winds) else "情報なし",
                            "波": waves[idx] if idx < len(waves) else "情報なし",
                            "降水確率": pops[idx] if idx < len(pops) else "情報なし",
                            "信頼度": reliabilities[idx] if idx < len(reliabilities) else "情報なし",
                            "温度": temps[idx] if idx < len(temps) else "情報なし"
                        }

    # 辞書からデータを取り出して表示
    weather_info_controls = []
    for key, value in weather_info_dict.items():
        day_info = "\n".join([f"{k}: {v}" for k, v in value.items()])
        weather_info_controls.append(ft.Text(value=day_info))

    if not weather_info_controls:
        page.add(ft.Text("天気データがありません。"))
    else:
        # ページに結果を表示
        page.add(
            ft.Column(
                controls=[
                    ft.Text(value="地域別天気データ"),
                    *weather_info_controls  # 各日の天気データを追加
                ]
            )
        )

# Fletアプリを開始
ft.app(target=main)
