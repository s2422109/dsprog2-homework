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
            print(f"[SUCCESS] 天気データ取得成功: {region_id}")
            return response.json()
        else:
            print(f"[ERROR] 天気データ取得失敗: ステータスコード {response.status_code} - {region_id}")
            return None
    except Exception as e:
        print(f"[EXCEPTION] 天気データ取得中にエラー発生: {e} - {region_id}")
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

# 天気情報の抽出関数（詳細表示用）
def extract_detailed_weather(weather_data):
    detailed_info = []
    if not isinstance(weather_data, list):
        return detailed_info

    weather_entry = weather_data[0]  # 最初の要素を使用
    publishing_office = weather_entry.get("publishingOffice", "不明")
    report_datetime = weather_entry.get("reportDatetime", "不明")
    time_series = weather_entry.get("timeSeries", [])

    for series in time_series:
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
                detailed_info.append(
                    {
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
                )
    return detailed_info

# GUIアプリケーションを構築
def main(page: ft.Page):
    page.title = "地域別天気データ"
    page.scroll = ft.ScrollMode.AUTO

    # 地域IDを取得
    region_data = fetch_region_data()
    if not region_data:
        page.add(ft.Text("地域データの取得に失敗しました。"))
        return

    # class10s と class15s と class20s の取得
    centers = region_data.get("centers", {})
    class15s = region_data.get("class15s", {})
    class20s = region_data.get("class20s", {})

    # class10s IDのリストを取得
    class10_ids = region_data.get("offices", {}).keys()

    # 天気情報を辞書に保存
    weather_info_dict = {}

    # 各地域の天気データを取得し辞書に保存
    for region_id in class10_ids:
        weather_data = fetch_weather_data(region_id)
        if weather_data:
            detailed_weather = extract_detailed_weather(weather_data)
            weather_info_dict[region_id] = detailed_weather
        else:
            weather_info_dict[region_id] = None  # データがない場合は None

    # 地域ごとのタブを作成
    regional_tabs = []
    for center_id, center_info in centers.items():
        region_name = center_info.get("name", "不明な地方")
        child_tabs = []

        for child_id in center_info.get("children", []):
            child_info = region_data.get("offices", {}).get(child_id, {})
            child_name = child_info.get("name", "不明な場所")
            sub_tabs = []

            for sub_child_id in child_info.get("children", []):
                sub_child_info = region_data.get("class10s", {}).get(sub_child_id, {})
                sub_child_name = sub_child_info.get("name", "不明な場所")
                sub_sub_tabs = []

                for sub_class15_id in sub_child_info.get("children", []):
                    sub_class15_info = class15s.get(sub_class15_id, {})
                    sub_class15_name = sub_class15_info.get("name", "不明な場所")
                    sub_class20_tabs = []

                    for sub_class20_id in sub_class15_info.get("children", []):
                        sub_class20_info = class20s.get(sub_class20_id, {})
                        sub_class20_name = sub_class20_info.get("name", "不明な場所")
                        # 天気データの取得
                        weather_for_region = weather_info_dict.get(child_id)
                        if weather_for_region:
                            weather_controls = []
                            for weather in weather_for_region:
                                if weather.get("エリア", "") in sub_class20_name:
                                    weather_text = "\n".join([f"{k}: {v}" for k, v in weather.items()])
                                    weather_controls.append(ft.Text(value=weather_text))
                        else:
                            weather_controls = [ft.Text("天気情報がありません。")]
                        # class10s のタブをサブタブに追加
                        sub_class20_tabs.append(
                            ft.Tab(
                                text=sub_class20_name,
                                content=ft.Column([
                                    ft.Text("天気情報:"),
                                    *weather_controls,
                                ])
                            )
                        )
                        

                    # class15s のタブをclass20sに追加
                    sub_sub_tabs.append(
                        ft.Tab(
                            text=sub_class15_name,
                            content=ft.Tabs(
                                tabs=sub_class20_tabs,
                                scrollable=True
                            )
                        )
                    )

                # 天気データの取得
                weather_for_region = weather_info_dict.get(child_id)
                if weather_for_region:
                    weather_controls = []
                    for weather in weather_for_region:
                        if sub_child_name in weather.get("エリア", ""):
                            weather_text = "\n".join([f"{k}: {v}" for k, v in weather.items()])
                            weather_controls.append(ft.Text(value=weather_text))
                else:
                    weather_controls = [ft.Text("天気情報がありません。")]

                # class10s のタブをサブタブに追加
                sub_tabs.append(
                    ft.Tab(
                        text=sub_child_name,
                        content=ft.Column([
                            ft.Text("天気情報:"),
                            *weather_controls,
                            ft.Tabs(
                                tabs=sub_sub_tabs,
                                scrollable=True
                            )
                        ])
                    )
                )

            # 子タブにサブタブを追加
            child_tabs.append(
                ft.Tab(
                    text=child_name,
                    content=ft.Tabs(
                        tabs=sub_tabs,
                        scrollable=True
                    )
                )
            )

        # 地方タブに追加
        regional_tabs.append(
            ft.Tab(
                text=region_name,
                content=ft.Tabs(
                    tabs=child_tabs,
                    scrollable=True
                )
            )
        )

    # ページにタブを追加
    page.add(
        ft.Tabs(
            tabs=regional_tabs,
            scrollable=True
        )
    )

# Fletアプリを開始
ft.app(target=main)
