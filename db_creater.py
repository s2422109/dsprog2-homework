import sqlite3
import requests

# 地域データ管理クラス
class RegionDataManager:
    DB_PATH = "region_data.db"
    AREA_JSON_URL = "http://www.jma.go.jp/bosai/common/const/area.json"

    def __init__(self):
        self.connection = sqlite3.connect(self.DB_PATH)
        self.cursor = self.connection.cursor()
        self.initialize_database()

    def initialize_database(self):
        """データベースの初期化"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                centers_name TEXT,
                centers_id TEXT,
                offices_name TEXT,
                offices_id TEXT,
                class10s_name TEXT,
                class10s_id TEXT,
                class15s_name TEXT,
                class15s_id TEXT,
                class20s_name TEXT,
                class20s_id TEXT
            )
        """)
        self.connection.commit()

    def fetch_region_data(self):
        """地域データを取得"""
        try:
            response = requests.get(self.AREA_JSON_URL)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[ERROR] 地域データ取得失敗: ステータスコード {response.status_code}")
                return None
        except Exception as e:
            print(f"[EXCEPTION] 地域データ取得中にエラー発生: {e}")
            return None

    def save_to_database(self, region_data):
        """地域データをデータベースに保存"""
        if not region_data:
            print("[ERROR] 地域データが空です。")
            return

        centers = region_data.get("centers", {})
        offices = region_data.get("offices", {})
        class10s = region_data.get("class10s", {})
        class15s = region_data.get("class15s", {})
        class20s = region_data.get("class20s", {})

        # centers をループ
        for center_id, center_info in centers.items():
            center_name = center_info.get("name", "")
            children_offices = center_info.get("children", [])

            # offices をループ
            for office_id in children_offices:
                office_info = offices.get(office_id, {})
                office_name = office_info.get("name", "")
                children_class10s = office_info.get("children", [])

                # class10s をループ
                for class10_id in children_class10s:
                    class10_info = class10s.get(class10_id, {})
                    class10_name = class10_info.get("name", "")
                    children_class15s = class10_info.get("children", [])

                    # class15s をループ
                    for class15_id in children_class15s:
                        class15_info = class15s.get(class15_id, {})
                        class15_name = class15_info.get("name", "")
                        children_class20s = class15_info.get("children", [])

                        # class20s をループ
                        for class20_id in children_class20s:
                            class20_info = class20s.get(class20_id, {})
                            class20_name = class20_info.get("name", "")

                            # データベースに挿入
                            self.cursor.execute("""
                                INSERT INTO areas (
                                    centers_name, centers_id, offices_name, offices_id,
                                    class10s_name, class10s_id, class15s_name, class15s_id,
                                    class20s_name, class20s_id
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                center_name, center_id, office_name, office_id,
                                class10_name, class10_id, class15_name, class15_id,
                                class20_name, class20_id
                            ))
        self.connection.commit()

    def close_connection(self):
        """データベース接続を閉じる"""
        self.connection.close()

class WeatherDataManager:
    DB_NAME = 'weather_data.db'
    AREA_URL = "http://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"  # URL with dynamic area ID

    def __init__(self):
        self.connection = sqlite3.connect(self.DB_NAME)
        self.cursor = self.connection.cursor()

    def create_table(self, table_name, columns):
        """動的にテーブルを作成"""
        columns_str = ", ".join([f"{col[0]} {col[1]}" for col in columns])
        print(f"Columns for table {table_name}: {columns}")
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
                    reliabilities = area.get("reliabilities", [])

                    # 各リストの長さを確認し、最も長いリストの長さに合わせる
                    max_len = max(len(weather_codes), len(weathers), len(winds), len(waves), len(pops), len(time_defines))
                    
                    # 各リストが不足している分、Noneで埋める
                    weather_codes += [None] * (max_len - len(weather_codes))
                    weathers += [None] * (max_len - len(weathers))
                    winds += [None] * (max_len - len(winds))
                    waves += [None] * (max_len - len(waves))
                    pops += [None] * (max_len - len(pops))  # `pop`のリストも埋める
                    temps += [None] * (max_len - len(temps))  # `temp`のリストも埋める
                    reliabilities += [None] * (max_len - len(reliabilities))  # `reliabilities`のリストも埋める

                    # 各timeDefineに対応する情報を保存
                    for idx, time_define in enumerate(time_defines):
                        weather_code = weather_codes[idx]
                        weather = weathers[idx]
                        wind = winds[idx]
                        wave = waves[idx]
                        pop = pops[idx]  # `pop`も収集
                        temp = temps[idx]  # `temp`も収集
                        reliability = reliabilities[idx]  # `reliabilities`も収集

                        # `weather`と`wind`が必要な場合にのみ保存
                        if (need == "weather" and weather is not None) or (need == "wind" and wind is not None) or (need == "pop" and pop is not None) or (need == "temp" and temp is not None) or (need == "reliabilities" and reliability is not None):
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
                                "pop": pop,  # `pop`は収集しつつ、テーブルには保存しない
                                "temp": temp,  # `temp`も収集しつつ、テーブルには保存しない
                                "reliabilities": reliability  # `reliabilities`も収集しつつ、テーブルには保存しない
                            })

                            # カラム名を全て追跡
                            all_columns.update(["offices_code", "publishing_office", "report_datetime", "area_name", "time_define", 
                                                "weather_code", "weather", "wind", "wave", "pop", "temp", "reliabilities"])

        # `weather_columns`に基づいてカラムを選定
        filtered_columns = [col[0] for col in weather_columns if col[0] in all_columns]
        print(filtered_columns)
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

# 実行部分
if __name__ == "__main__":
    # 地域データを管理
    region_manager = RegionDataManager()
    print("[INFO] 地域データを取得中...")
    region_data = region_manager.fetch_region_data()

    if region_data:
        print("[INFO] データをデータベースに保存中...")
        region_manager.save_to_database(region_data)
        print("[SUCCESS] 地域データの保存が完了しました。")

    # 全オフィスのIDをリストに格納
    offices = []
    centers = region_data.get("centers", {})
    offices_data = region_data.get("offices", {})

    # 各センター内のオフィスIDを収集
    for center_info in centers.values():
        children_offices = center_info.get("children", [])
        offices.extend(children_offices)

    print(f"[INFO] オフィスコードリスト: {offices}")

    region_manager.close_connection()

    # 天気データを管理
    weather_manager = WeatherDataManager()
    table_structure = {
        "weather_info": [
            ("offices_code", "TEXT"),
            ("publishing_office", "TEXT"),
            ("report_datetime", "TEXT"),
            ("area_name", "TEXT"),
            ("time_define", "TEXT"),
            ("weather_code", "TEXT"),
            ("weather", "TEXT"),
            ("wind", "TEXT"),
            ("wave", "TEXT")
        ],
        "weather_pops": [
            ("offices_code", "TEXT"),
            ("publishing_office", "TEXT"),
            ("report_datetime", "TEXT"),
            ("area_name", "TEXT"),
            ("time_define", "TEXT"),
            ("pop", "TEXT")
        ],
        "weather_temps": [
            ("offices_code", "TEXT"),
            ("publishing_office", "TEXT"),
            ("report_datetime", "TEXT"),
            ("area_name", "TEXT"),
            ("time_define", "TEXT"),
            ("temp", "TEXT")
        ],
        "weather_reliabilities": [
            ("offices_code", "TEXT"),
            ("publishing_office", "TEXT"),
            ("report_datetime", "TEXT"),
            ("area_name", "TEXT"),
            ("time_define", "TEXT"),
            ("weather_code", "TEXT"),
            ("pop", "TEXT"),
            ("reliabilities", "TEXT")
        ]
    }
    print("[INFO] 天気データを取得中...")
    for table_name, columns in table_structure.items():  # 正しく2つにアンパック
        print(f"[INFO] テーブル {table_name} を作成中...")
        print(f"[INFO] カラム: {columns}")
        weather_manager.create_table(table_name, columns)
        for office in offices:
            print(f"[INFO] {office} の天気データを取得中...")
            weather_data = weather_manager.fetch_weather_data(office)
            if weather_data:
                # 必要なカラムを決定（例: テーブルごとの必要なデータをマッピング）
                if table_name == "weather_info":
                    need = "weather"
                elif table_name == "weather_pops":
                    need = "pop"
                elif table_name == "weather_temps":
                    need = "temp"
                elif table_name == "weather_reliabilities":
                    need = "reliabilities"

                weather_manager.save_weather_to_db(table_name, columns, weather_data, need)
                print(f"[SUCCESS] {office} のデータを {table_name} に保存しました。")
            else:
                print(f"[ERROR] {office} の天気データの取得に失敗しました。")



    weather_manager.close_connection()
