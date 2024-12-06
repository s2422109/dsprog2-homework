import sqlite3
import requests
import flet as ft

# 地域情報のURL
AREA_URL_TEMPLATE = "http://www.jma.go.jp/bosai/forecast/data/forecast/{region_id}.json"

# データベース管理クラス
class DatabaseManager:
    def __init__(self, db_path="region_data.db"):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

    def fetch_region_hierarchy(self):
        """地域階層情報をデータベースから取得"""
        centers = {}
        self.cursor.execute("SELECT centers_name, centers_id, offices_name, offices_id, class10s_name, class10s_id FROM areas")
        rows = self.cursor.fetchall()
        for row in rows:
            center_name, center_id, office_name, office_id, class10_name, class10_id = row

            if center_id not in centers:
                centers[center_id] = {"name": center_name, "children": {}}
            if office_id not in centers[center_id]["children"]:
                centers[center_id]["children"][office_id] = {"name": office_name, "children": {}}
            if class10_id:
                centers[center_id]["children"][office_id]["children"][class10_id] = {"name": class10_name}
        return centers

    def close(self):
        self.connection.close()


# 天気データを取得する関数
def fetch_weather_data(region_id):
    url = AREA_URL_TEMPLATE.format(region_id=region_id)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"[EXCEPTION] 天気データ取得中にエラー発生: {e}")
        return None

# GUIアプリケーション
def main(page: ft.Page):
    page.title = "地域別天気データ"
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.START

    db_manager = DatabaseManager()

    # 地域データの取得
    region_data = db_manager.fetch_region_hierarchy()
    db_manager.close()

    # 地域データが空の場合の処理
    if not region_data:
        page.add(ft.Text("データベースに地域データがありません。"))
        return

    # 選択した地域の天気データを表示するためのテキスト
    weather_display = ft.Text("天気情報を選択してください。", expand=True)

    def display_weather_data(region_id):
        weather_data = fetch_weather_data(region_id)
        if weather_data:
            # 天気情報を抽出して表示
            detailed_weather = extract_detailed_weather(weather_data)
            if detailed_weather:
                weather_text = "\n\n".join(
                    ["\n".join([f"{k}: {v}" for k, v in item.items()]) for item in detailed_weather]
                )
                weather_display.value = weather_text
            else:
                weather_display.value = "天気情報が見つかりません。"
        else:
            weather_display.value = "天気情報の取得に失敗しました。"
        page.update()

    # サイドバーの作成
    expansion_tiles = []
    for center_id, center_info in region_data.items():
        center_name = center_info["name"]
        office_tiles = []

        for office_id, office_info in center_info["children"].items():
            office_name = office_info["name"]
            class10_tiles = []

            for class10_id, class10_info in office_info["children"].items():
                class10_name = class10_info["name"]

                # `class10s` レベルの地域タイル
                class10_tiles.append(
                    ft.ListTile(
                        title=ft.Text(class10_name),
                        on_click=lambda e, rid=class10_id: display_weather_data(rid),
                    )
                )

            # `offices` レベルの地域タイル
            office_tiles.append(
                ft.ExpansionTile(
                    title=ft.Text(office_name),
                    controls=class10_tiles,
                )
            )

        # `centers` レベルの地域タイル
        expansion_tiles.append(
            ft.ExpansionTile(
                title=ft.Text(center_name),
                controls=office_tiles,
            )
        )

    # サイドバーを上部固定にするためのレイアウト
    page.add(
        ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        expansion_tiles,
                        expand=True,
                    ),
                    width=300,
                    height=600,
                    alignment=ft.alignment.top_left,
                    expand=False,
                ),
                ft.VerticalDivider(width=1),
                ft.Container(
                    content=weather_display,
                    expand=True,
                    alignment=ft.alignment.center,
                ),
            ],
            expand=True,
        )
    )


# 天気情報の抽出関数
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
            weather_codes = area.get("weatherCodes", [])
            weathers = area.get("weathers", [])
            for idx, time_define in enumerate(time_defines):
                detailed_info.append(
                    {
                        "発表局": publishing_office,
                        "発表日時": report_datetime,
                        "エリア": area_name,
                        "日時": time_define,
                        "天気コード": weather_codes[idx] if idx < len(weather_codes) else "情報なし",
                        "天気": weathers[idx] if idx < len(weathers) else "情報なし",
                    }
                )
    return detailed_info

# Fletアプリを開始
ft.app(target=main)
