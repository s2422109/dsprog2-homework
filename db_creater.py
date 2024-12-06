import sqlite3
import requests

# 地域データ管理クラス
class RegionDataManager:

    AREA_JSON_URL = "http://www.jma.go.jp/bosai/common/const/area.json"

    def __init__(self,database_name):
        self.database_name = database_name
        self.connection = sqlite3.connect(database_name)
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
    AREA_URL = "http://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"
    def __init__(self,database_name):
        self.database_name = database_name
        self.connection = sqlite3.connect(database_name)
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


class WeatherDataFetcher:
    AREA_URL = "http://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

    def __init__(self, database_name):
        self.database_name = database_name
        self.setup_database()

    # SQLiteデータベースをセットアップ
    def setup_database(self):
        conn = sqlite3.connect(self.database_name)
        cursor = conn.cursor()
        
        # weather_tt テーブルの作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_tt (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offices_code TEXT,
                publishing_office TEXT,
                report_datetime TEXT,
                area_name TEXT,
                time_define TEXT,
                temps_min TEXT,
                temps_min_upper TEXT,
                temps_min_lower TEXT,
                temps_max TEXT,
                temps_max_upper TEXT,
                temps_max_lower TEXT
            )
        """)
        
        # weather_temp_ave テーブルの作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_temp_ave (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offices_code TEXT,
                publishing_office TEXT,
                report_datetime TEXT,
                area_name TEXT,
                temps_ave_min TEXT,
                temps_ave_max TEXT
            )
        """)
        
        # weather_pop_ave テーブルの作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_pop_ave (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offices_code TEXT,
                publishing_office TEXT,
                report_datetime TEXT,
                area_name TEXT,
                temps_pop_min TEXT,
                temps_pop_max TEXT
            )
        """)
        
        conn.commit()
        conn.close()

    def save_weather_data(self, table_name, data):
        conn = sqlite3.connect(self.database_name)
        cursor = conn.cursor()

        # テーブルの列名を取得する
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]  # 列名のリストを作成
        
        # データの長さが列数と一致していることを確認
        for row in data:
            if len(row) != len(column_names) - 1:  # id列は除外するため -1
                print(f"[ERROR] データの長さが列数と一致しません: {len(row)} != {len(column_names) - 1}")
                return

        # 挿入するためのプレースホルダーを作成
        placeholders = ", ".join(["?" for _ in range(len(column_names) - 1)])  # id列を除く
        sql = f"INSERT INTO {table_name} ({', '.join(column_names[1:])}) VALUES ({placeholders})"  # id列を除く

        # データの挿入
        cursor.executemany(sql, data)
        conn.commit()
        conn.close()


    # 天気データを取得する関数
    def fetch_weather_data(self, office_code):
        """天気データを取得"""
        url = self.AREA_URL.format(office_code)
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

    # メイン処理
    def process_weather_data(self):
        if weather_data and isinstance(weather_data, list) and len(weather_data) > 1:
            print(f"[INFO] 'weather_data'の処理を開始します。")
            second_entry = weather_data[1]

            # 発表局と発表日時
            publishing_office = second_entry.get("publishingOffice", "不明")
            report_datetime = second_entry.get("reportDatetime", "不明")
            time_series = second_entry.get("timeSeries", [])
            temp_average = second_entry.get("tempAverage", {})
            precip_average = second_entry.get("precipAverage", {})

            weather_tt_data = []
            weather_temp_ave_data = []
            weather_pop_ave_data = []

            # timeSeriesの処理
            for series in time_series:
                time_defines = series.get("timeDefines", [])
                areas = series.get("areas", [])

                for area in areas:
                    area_name = area.get("area", {}).get("name", "不明")
                    area_code = area.get("area", {}).get("code", "不明")

                    temps_min = area.get("tempsMin", [])
                    temps_min_upper = area.get("tempsMinUpper", [])
                    temps_min_lower = area.get("tempsMinLower", [])
                    temps_max = area.get("tempsMax", [])
                    temps_max_upper = area.get("tempsMaxUpper", [])
                    temps_max_lower = area.get("tempsMaxLower", [])

                    for idx, time_define in enumerate(time_defines):
                        # 「情報なし」が含まれている場合は追加しない
                        if any(val == "情報なし" for val in [
                            temps_min[idx] if idx < len(temps_min) else "情報なし",
                            temps_min_upper[idx] if idx < len(temps_min_upper) else "情報なし",
                            temps_min_lower[idx] if idx < len(temps_min_lower) else "情報なし",
                            temps_max[idx] if idx < len(temps_max) else "情報なし",
                            temps_max_upper[idx] if idx < len(temps_max_upper) else "情報なし",
                            temps_max_lower[idx] if idx < len(temps_max_lower) else "情報なし"
                        ]):
                            continue  # 情報なしが含まれていればこのデータはスキップ

                        weather_tt_data.append((
                            area_code, publishing_office, report_datetime,
                            area_name, time_define,
                            temps_min[idx] if idx < len(temps_min) else "情報なし",
                            temps_min_upper[idx] if idx < len(temps_min_upper) else "情報なし",
                            temps_min_lower[idx] if idx < len(temps_min_lower) else "情報なし",
                            temps_max[idx] if idx < len(temps_max) else "情報なし",
                            temps_max_upper[idx] if idx < len(temps_max_upper) else "情報なし",
                            temps_max_lower[idx] if idx < len(temps_max_lower) else "情報なし"
                        ))

            # tempAverageの処理
            for area in temp_average.get("areas", []):
                area_name = area.get("area", {}).get("name", "不明")
                area_code = area.get("area", {}).get("code", "不明")
                min_temp = area.get("min", "情報なし")
                max_temp = area.get("max", "情報なし")

                if min_temp != "情報なし" and max_temp != "情報なし":  # 「情報なし」含まれていない場合のみ追加
                    weather_temp_ave_data.append((
                        area_code, publishing_office, report_datetime,
                        area_name,   # time_defineは不明
                        min_temp,
                        max_temp
                    ))

            # precipAverageの処理
            for area in precip_average.get("areas", []):
                area_name = area.get("area", {}).get("name", "不明")
                area_code = area.get("area", {}).get("code", "不明")
                min_precip = area.get("min", "情報なし")
                max_precip = area.get("max", "情報なし")

                if min_precip != "情報なし" and max_precip != "情報なし":  # 「情報なし」含まれていない場合のみ追加
                    weather_pop_ave_data.append((
                        area_code, publishing_office, report_datetime,
                        area_name,   # time_defineは不明
                        min_precip,
                        max_precip
                    ))

            # データベースに保存
            if weather_tt_data:
                self.save_weather_data("weather_tt", weather_tt_data)
            if weather_temp_ave_data:
                self.save_weather_data("weather_temp_ave", weather_temp_ave_data)
            if weather_pop_ave_data:
                self.save_weather_data("weather_pop_ave", weather_pop_ave_data)

            print("[INFO] 有効な天気データがデータベースに保存されました。")
        else:
            print("[ERROR] 天気データの取得に失敗しました。")



# 実行部分
if __name__ == "__main__":
    # 地域データを管理
    DB_PATH = "region_data.db"
    region_manager = RegionDataManager(DB_PATH)
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

    # 天気データを管理
    weather_manager = WeatherDataManager(DB_PATH)
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
    
    # WeatherDataFetcherインスタンスを作成して実行
    weather_fetcher = WeatherDataFetcher(DB_PATH)
    for office in offices:
        print(f"[INFO] {office} の天気データを取得中...")
        weather_data = weather_fetcher.fetch_weather_data(office)  # officeを引数として渡す
        if weather_data:
            weather_fetcher.process_weather_data()  # weather_dataを引数として渡す
            print(f"[SUCCESS] {office} のデータを取得しました。")
        else:
            print(f"[ERROR] {office} の天気データの取得に失敗しました。")
    


    weather_manager.close_connection()
