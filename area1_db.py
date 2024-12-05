import requests
import sqlite3

class WeatherDataManager:
    DB_NAME = 'weather_data.db'
    AREA_URL = "http://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"  # URL with dynamic area ID

    def __init__(self):
        self.connection = sqlite3.connect(self.DB_NAME)
        self.cursor = self.connection.cursor()

    def create_table(self, table_name, columns):
        """動的にテーブルを作成"""
        columns_str = ", ".join([f"{col[0]} {col[1]}" for col in columns])
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns_str})"
        self.cursor.execute(create_sql)
        self.connection.commit()

    def fetch_weather_data(self, office_code):
        """天気データを取得"""
        url = self.AREA_URL.format(office_code)
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

    def save_data_to_db(self, table_name, columns, data):
        """動的なデータの保存"""
        placeholders = ", ".join(["?" for _ in columns])  # プレースホルダー
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        for record in data:
            values = [record.get(col, None) for col in columns]
            self.cursor.execute(insert_sql, values)
        self.connection.commit()

    def save_weather_to_db(self, table_name, weather_columns, data, need):
        """天気データをDBに保存"""
        weather_data = []
        all_columns = set()  # すべてのカラムを追跡するためのセット

        for weather_entry in data:
            publishing_office = weather_entry.get("publishingOffice", "不明")
            report_datetime = weather_entry.get("reportDatetime", "不明")
            time_series = weather_entry.get("timeSeries", [])

            if not time_series:
                print("[ERROR] 'timeSeries'が見つかりませんでした")
                continue

            for series in time_series:
                time_defines = series.get("timeDefines", [])
                areas = series.get("areas", [])

                for area in areas:
                    area_name = area.get("area", {}).get("name", "不明")
                    offices_code = area.get("area", {}).get("code", "不明")

                    # 各データリストを取得
                    weather_codes = area.get("weatherCodes", [])
                    weathers = area.get("weathers", [])
                    winds = area.get("winds", [])
                    waves = area.get("waves", [])
                    pops = area.get("pops", [])
                    temps = area.get("temps", [])

                    # 各リストの長さを確認し、最も長いリストの長さに合わせる
                    max_len = max(len(weather_codes), len(weathers), len(winds), len(waves), len(pops), len(time_defines))
                    
                    # 各リストが不足している分、Noneで埋める
                    weather_codes += [None] * (max_len - len(weather_codes))
                    weathers += [None] * (max_len - len(weathers))
                    winds += [None] * (max_len - len(winds))
                    waves += [None] * (max_len - len(waves))
                    pops += [None] * (max_len - len(pops))  # `pop`のリストも埋める
                    temps += [None] * (max_len - len(temps))  # `temp`のリストも埋める

                    # 各timeDefineに対応する情報を保存
                    for idx, time_define in enumerate(time_defines):
                        weather_code = weather_codes[idx]
                        weather = weathers[idx]
                        wind = winds[idx]
                        wave = waves[idx]
                        pop = pops[idx]  # `pop`も収集
                        temp = temps[idx]  # `temp`も収集

                        # `weather`と`wind`が必要な場合にのみ保存
                        if (need == "temp" and temp is not None):
                            # レコードの作成
                            weather_data.append({
                                "offices_code": offices_code,
                                "publishing_office": publishing_office,
                                "report_datetime": report_datetime,
                                "area_name": area_name,
                                "time_define": time_define,
                                "weather_code": weather_code,
                                "weather": weather,
                                "wind": wind,
                                "wave": wave,
                                "temp": temp  # `pop`は収集しつつ、テーブルには保存しない
                            })

                            # カラム名を全て追跡
                            all_columns.update(["offices_code", "publishing_office", "report_datetime", "area_name", "time_define", 
                                                "weather_code", "weather", "wind", "wave", "temp"])

        # `weather_columns`に基づいてカラムを選定
        filtered_columns = [col[0] for col in weather_columns if col[0] in all_columns]

        # テーブルの作成（`weather_columns`にあるカラムのみで作成）
        weather_columns_filtered = [(col, "TEXT") for col in filtered_columns]
        self.create_table(table_name, weather_columns_filtered)

        # データの保存（`weather_columns`にあるカラムのみ保存）
        filtered_weather_data = [
            {key: value for key, value in record.items() if key in filtered_columns} for record in weather_data
        ]
        self.save_data_to_db(table_name, filtered_columns, filtered_weather_data)

    def close_connection(self):
        """データベース接続を閉じる"""
        self.connection.close()


# 使用例
if __name__ == "__main__":
    manager = WeatherDataManager()

    # テーブル名とカラムを外部から渡す
    table_name = "weather_info"
    weather_columns = [
        ("offices_code", "TEXT"),
        ("publishing_office", "TEXT"),
        ("report_datetime", "TEXT"),
        ("area_name", "TEXT"),
        ("time_define", "TEXT"),
        ("weather_code", "TEXT"),
        ("weather", "TEXT"),
        ("wind", "TEXT"),
        ("wave", "TEXT"),
        ("temp", "TEXT")
    ]

    # `need`に必要なカラムを指定
    need = ['temp']  # `weather`と`wind`が存在する場合のみデータを保存

    # テーブル作成（指定されたカラムのみ作成）
    manager.create_table(table_name, weather_columns)

    # 天気データの取得
    office_code = "011000"  # 例: office_code
    weather_data = manager.fetch_weather_data(office_code)

    if weather_data:
        manager.save_weather_to_db(table_name, weather_columns, weather_data, need)
        print("[SUCCESS] 天気データの保存が完了しました。")
    else:
        print("[ERROR] 天気データの取得に失敗しました。")

    # 接続を閉じる
    manager.close_connection()
