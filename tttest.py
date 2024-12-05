import requests
import flet as ft

# 地域情報のURL
AREA_URL = "http://www.jma.go.jp/bosai/forecast/data/forecast/011000.json"

# JSONデータを取得する関数
def fetch_weather_data():
    print(f"[INFO] 天気データを取得中: {AREA_URL}")
    try:
        response = requests.get(AREA_URL)
        if response.status_code == 200:
            print(f"[SUCCESS] 天気データ取得成功")
            return response.json()
        else:
            print(f"[ERROR] 天気データ取得失敗: ステータスコード {response.status_code}")
            return None
    except Exception as e:
        print(f"[EXCEPTION] 天気データ取得中にエラー発生: {e}")
        return None


# GUIアプリケーションを構築
def main(page: ft.Page):
    page.title = "地域タブの階層表示"
    page.scroll = ft.ScrollMode.AUTO

    # 天気データの取得
    weather_data = fetch_weather_data()

    if weather_data and isinstance(weather_data, list):
        print(f"[INFO] 'weather_data'はリスト型です。2つ目の辞書を処理します。")

        # 2つ目の辞書を取得
        if len(weather_data) > 1:
            second_entry = weather_data[1]

            # 発表局と発表日時
            publishing_office = second_entry.get("publishingOffice", "不明")
            report_datetime = second_entry.get("reportDatetime", "不明")
            time_series = second_entry.get("timeSeries", [])
            temp_average = second_entry.get("tempAverage", {})
            precip_average = second_entry.get("precipAverage", {})

            time_info_controls = []

            # timeSeriesが存在するか確認
            if not time_series:
                print("[ERROR] 'timeSeries'が見つかりませんでした")
            else:
                for series_index, series in enumerate(time_series):
                    time_defines = series.get("timeDefines", [])
                    areas = series.get("areas", [])

                    for area in areas:
                        area_name = area.get("area", {}).get("name", "不明")
                        area_code = area.get("area", {}).get("code", "不明")

                        # codeが'011000'のものをフィルタリング
                        if area_code == "11016":
                            temps_min = area.get("tempsMin", [])
                            temps_min_upper = area.get("tempsMinUpper", [])
                            temps_min_lower = area.get("tempsMinLower", [])
                            temps_max = area.get("tempsMax", [])
                            temps_max_upper = area.get("tempsMaxUpper", [])
                            temps_max_lower = area.get("tempsMaxLower", [])

                            # 各timeDefineに対応するデータを表示
                            for idx, time_define in enumerate(time_defines):
                                temp_info = {
                                    "日時": time_define,
                                    "最低気温": temps_min[idx] if idx < len(temps_min) else "情報なし",
                                    "最低気温上限": temps_min_upper[idx] if idx < len(temps_min_upper) else "情報なし",
                                    "最低気温下限": temps_min_lower[idx] if idx < len(temps_min_lower) else "情報なし",
                                    "最高気温": temps_max[idx] if idx < len(temps_max) else "情報なし",
                                    "最高気温上限": temps_max_upper[idx] if idx < len(temps_max_upper) else "情報なし",
                                    "最高気温下限": temps_max_lower[idx] if idx < len(temps_max_lower) else "情報なし",
                                }

                                # 表示用の文字列を生成
                                time_info_controls.append(
                                    ft.Text(
                                        value=f"日時: {temp_info['日時']}\n"
                                              f"最低気温: {temp_info['最低気温']}℃ "
                                              f"(上限: {temp_info['最低気温上限']}℃, 下限: {temp_info['最低気温下限']}℃)\n"
                                              f"最高気温: {temp_info['最高気温']}℃ "
                                              f"(上限: {temp_info['最高気温上限']}℃, 下限: {temp_info['最高気温下限']}℃)\n"
                                    )
                                )

            # tempAverageとprecipAverageの処理
            if temp_average:
                for area in temp_average.get("areas", []):
                    area_name = area.get("area", {}).get("name", "不明")
                    area_code = area.get("area", {}).get("code", "不明")
                    if area_code == "11016":
                        min_temp = area.get("min", "情報なし")
                        max_temp = area.get("max", "情報なし")
                        time_info_controls.append(
                            ft.Text(
                                value=f"{area_name} - 平均最低気温: {min_temp}℃, 平均最高気温: {max_temp}℃"
                            )
                        )

            if precip_average:
                for area in precip_average.get("areas", []):
                    area_name = area.get("area", {}).get("name", "不明")
                    area_code = area.get("area", {}).get("code", "不明")
                    if area_code == "11016":
                        min_precip = area.get("min", "情報なし")
                        max_precip = area.get("max", "情報なし")
                        time_info_controls.append(
                            ft.Text(
                                value=f"{area_name} - 平均降水量: 最小 {min_precip}mm, 最大 {max_precip}mm"
                            )
                        )

            # ページにデータを表示
            page.add(
                ft.Column(
                    controls=[
                        ft.Text(f"発表局: {publishing_office}"),
                        ft.Text(f"発表日時: {report_datetime}"),
                        ft.Text("天気データ:"),
                        *time_info_controls
                    ]
                )
            )

        else:
            page.add(ft.Text("2つ目の辞書が存在しません。"))
    else:
        page.add(ft.Text("天気データの取得に失敗しました。"))


# Fletアプリを開始
ft.app(target=main)
