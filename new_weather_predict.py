import sqlite3
import requests
import flet as ft
import sys
import os
import subprocess
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from datetime import timedelta
# create_database.py
from db_creater import RegionDataManager, WeatherDataManager, WeatherDataFetcher


# SQLAlchemyのベースクラスを作成
Base = declarative_base()

def create_database():
    # データベースのパス
    DB_PATH = "region_data.db"
    
    try:
        # 地域データを管理
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
        for table_name, columns in table_structure.items():
            print(f"[INFO] テーブル {table_name} を作成中...")
            print(f"[INFO] カラム: {columns}")
            weather_manager.create_table(table_name, columns)
            for office in offices:
                print(f"[INFO] {office} の天気データを取得中...")
                weather_data = weather_manager.fetch_weather_data(office)
                if weather_data:
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
        
        # WeatherDataFetcherの実行部分を修正
        weather_fetcher = WeatherDataFetcher(DB_PATH)
        for office in offices:
            print(f"[INFO] {office} の天気データを取得中...")
            weather_data = weather_fetcher.fetch_weather_data(office)
            if weather_data:
                # weather_dataを引数として渡す
                weather_fetcher.process_weather_data(weather_data)  # ここを修正
                print(f"[SUCCESS] {office} のデータを取得しました。")
            else:
                print(f"[ERROR] {office} の天気データの取得に失敗しました。")

    finally:
        if 'weather_manager' in locals():
            weather_manager.close_connection()



def ensure_database_exists():
    """データベースファイルの存在確認とcreate_database.pyの実行"""
    db_path = "region_data.db"
    required_tables = []
    
    # 新規作成が必要かどうかのフラグ
    need_creation = False
    
    if os.path.exists(db_path):
        # データベースが存在する場合、中身を確認
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            # テーブルの存在確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            required_tables = ['areas', 'weather_info', 'weather_pops', 'weather_temps']
            
            # 必要なテーブルが全て存在し、データが入っているか確認
            if not all(table in tables for table in required_tables):
                need_creation = True
            else:
                for table in required_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    if cursor.fetchone()[0] == 0:
                        need_creation = True
                        break
        except sqlite3.Error:
            need_creation = True
        finally:
            conn.close()
    else:
        need_creation = True

    if not need_creation:
        print("有効なデータベースが存在します。既存のデータベースを使用します。")
        return True

    print("データベースの新規作成を開始します...")
    try:
        # 既存のファイルがある場合は削除
        if os.path.exists(db_path):
            os.remove(db_path)
            
        create_database()
        
        
        # 作成後の確認
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            try:
                for table in required_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    if cursor.fetchone()[0] == 0:
                        print(f"Error: {table}テーブルにデータがありません。")
                        return False
                print("データベースの作成が完了しました。")
                return True
            except sqlite3.Error as e:
                print(f"データベース確認中にエラー: {e}")
                return False
            finally:
                conn.close()
        return False
            
    except subprocess.CalledProcessError as e:
        print(f"データベース作成中にエラーが発生しました:")
        if e.stdout:
            print(f"標準出力: {e.stdout}")
        if e.stderr:
            print(f"エラー出力: {e.stderr}")
        return False
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        return False


# ORMモデルの定義
class Area(Base):
    __tablename__ = 'areas'
    
    id = Column(Integer, primary_key=True)
    centers_name = Column(String)
    centers_id = Column(Integer, ForeignKey('centers.id'))  # 外部キーを追加
    offices_name = Column(String)
    offices_id = Column(Integer, ForeignKey('offices.id'))  # 外部キーを追加
    class10s_name = Column(String)
    class10s_id = Column(Integer, ForeignKey('class10.id'))  # 外部キーを追加

    # relationships
    center = relationship('Center', back_populates='areas')
    office = relationship('Office', back_populates='areas')
    class10 = relationship('Class10', back_populates='areas')

class Center(Base):
    __tablename__ = 'centers'
    id = Column(Integer, primary_key=True)
    name = Column(String)

    # 各センターに関連するエリアを指定
    areas = relationship('Area', back_populates='center')

class Office(Base):
    __tablename__ = 'offices'
    id = Column(Integer, primary_key=True)
    name = Column(String)

    # 各オフィスに関連するエリアを指定
    areas = relationship('Area', back_populates='office')

class Class10(Base):
    __tablename__ = 'class10'
    id = Column(Integer, primary_key=True)
    name = Column(String)

    # 各クラス10に関連するエリアを指定
    areas = relationship('Area', back_populates='class10')

# データベース接続とセッション作成
DATABASE_URL = "sqlite:///region_data.db"  # ここを適切に設定
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# データベースのテーブル作成
Base.metadata.create_all(engine)


class DatabaseManager:
    def __init__(self, db_path="region_data.db"):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        ensure_database_exists()

    def connect(self):
        """データベースへの接続を開く"""
        if not self.connection:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            

    def fetch_region_hierarchy(self):
        """地域階層情報をデータベースから取得"""
        self.connect()  # 接続が開かれていることを確認
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

    def fetch_weather_info(self, class10_id):
        """特定の地域の気象情報を取得"""
        self.connect()  # 接続が開かれていることを確認
        self.cursor.execute("""
            SELECT wi.offices_code, wi.publishing_office, wi.report_datetime, wi.area_name,
                wi.time_define, wi.weather_code, wi.weather, wi.wind, wi.wave
            FROM weather_info wi
            JOIN areas a ON wi.offices_code = a.class10s_id
            WHERE a.class10s_id = ?
        """, (class10_id,))
        rows = self.cursor.fetchall()
        return rows

    def fetch_weather_pops(self, class10_id):
        """特定の地域の降水確率情報を取得"""
        self.connect()  # 接続が開かれていることを確認
        self.cursor.execute("""
            SELECT wi.offices_code, wi.publishing_office, wi.report_datetime, 
                wi.area_name, wi.time_define, wi.pop
            FROM weather_pops wi
            JOIN areas a ON wi.offices_code = a.class10s_id
            WHERE a.class10s_id = ?
        """, (class10_id,))
        rows = self.cursor.fetchall()
        return rows
    
    def fetch_weather_temps(self, class10_id):
        """特定の地域の気温情報を取得（class10の直下のclass20に対応）"""
        self.connect()
        self.cursor.execute("""
            SELECT wi.offices_code, wi.publishing_office, wi.report_datetime, 
                wi.area_name, wi.time_define, wi.temp, a.class20s_name
            FROM weather_temps wi
            JOIN areas a ON a.class20s_name LIKE '%' || wi.area_name || '%'
            WHERE a.class10s_id = ?
        """, (class10_id,))
        rows = self.cursor.fetchall()
        
        return rows
    
    def fetch_weather_reliabilities(self, office_id):
        """特定の地域の週間天気予報情報を取得"""
        self.connect()  # 接続が開かれていることを確認
        self.cursor.execute("""
            SELECT wr.offices_code, wr.publishing_office, wr.report_datetime, 
                   wr.area_name, wr.time_define, wr.weather_code, 
                   wr.pop, wr.reliabilities
            FROM weather_reliabilities wr
            JOIN areas a ON wr.offices_code = a.offices_id
            WHERE a.offices_id = ?
            ORDER BY wr.time_define
        """, (office_id,))
        rows = self.cursor.fetchall()
        return rows
    
    def fetch_weather_temps_by_name(self, class10_id):
        """class10_idに基づいて気温情報を検索"""
        self.connect()
        self.cursor.execute("""
            SELECT wt.offices_code, wt.publishing_office, wt.report_datetime, 
                   wt.area_name, wt.time_define, 
                   wt.temps_min, wt.temps_min_upper, wt.temps_min_lower,
                   wt.temps_max, wt.temps_max_upper, wt.temps_max_lower
            FROM weather_tt wt
            JOIN areas a ON a.class20s_name LIKE '%' || wt.area_name || '%'
            WHERE a.class10s_id = ?
        """, (class10_id,))
        return self.cursor.fetchall()

    def fetch_temp_averages(self, class10_id):
        """class10_idに基づいて平均気温情報を検索"""
        self.connect()
        self.cursor.execute("""
            SELECT DISTINCT wta.temps_ave_min, wta.temps_ave_max, wta.report_datetime, wta.area_name
            FROM weather_temp_ave wta
            JOIN areas a ON a.class20s_name LIKE '%' || wta.area_name || '%'
            WHERE a.class10s_id = ?
            ORDER BY wta.report_datetime DESC
        """, (class10_id,))
        return self.cursor.fetchall()

    def fetch_pop_averages(self, class10_id):
        """class10_idに基づいて降水確率情報を検索"""
        self.connect()
        self.cursor.execute("""
            SELECT DISTINCT wpa.temps_pop_min, wpa.temps_pop_max, wpa.report_datetime, wpa.area_name
            FROM weather_pop_ave wpa
            JOIN areas a ON a.class20s_name LIKE '%' || wpa.area_name || '%'
            WHERE a.class10s_id = ?
            ORDER BY wpa.report_datetime DESC
        """, (class10_id,))
        return self.cursor.fetchall()

    def close(self):
        """データベース接続を閉じる"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None


# サイドバーを構築するクラス
class Sidebar:
    def __init__(self, region_data, on_selection_change):
        self.region_data = region_data
        self.on_selection_change = on_selection_change
        self.is_processing = False  # 処理状態を追跡
        self.controls = []  # サイドバーのコントロールを保持

    def set_processing_state(self, is_processing):
        """処理状態を設定し、コントロールの有効/無効を切り替える"""
        self.is_processing = is_processing
        for control in self.controls:
            control.disabled = is_processing
        # サイドバーの更新をトリガー
        if hasattr(self, 'sidebar_container'):
            self.sidebar_container.update()

    def on_tile_click(self, e, center_id, office_id, class10_id):
        """タイル選択時の処理"""
        if not self.is_processing:
            self.set_processing_state(True)  # 処理開始時に無効化
            self.on_selection_change(center_id, office_id, class10_id, self)

    def build_sidebar(self):
        """サイドバーを作成"""
        expansion_tiles = []
        self.controls = []  # コントロールリストをリセット

        for center_id, center_info in self.region_data.items():
            center_name = center_info["name"]
            office_tiles = []

            for office_id, office_info in center_info["children"].items():
                office_name = office_info["name"]
                class10_tiles = []

                for class10_id, class10_info in office_info["children"].items():
                    class10_name = class10_info["name"]
                    
                    # class10sレベルのタイル
                    tile = ft.ListTile(
                        title=ft.Text(class10_name, color=ft.colors.WHITE),
                        on_click=lambda e, c=center_id, o=office_id, cl=class10_id: 
                            self.on_tile_click(e, c, o, cl),
                    )
                    class10_tiles.append(tile)
                    self.controls.append(tile)

                # officesレベルのタイル
                office_expansion = ft.ExpansionTile(
                    title=ft.Text(office_name, color=ft.colors.WHITE),
                    controls=class10_tiles,
                )
                office_tiles.append(office_expansion)
                self.controls.append(office_expansion)

            # centersレベルのタイル
            center_expansion = ft.ExpansionTile(
                title=ft.Text(center_name, color=ft.colors.WHITE),
                controls=office_tiles,
            )
            expansion_tiles.append(center_expansion)
            self.controls.append(center_expansion)

        # サイドバーコンテナを保持
        self.sidebar_container = ft.Container(
            content=ft.ListView(
                controls=expansion_tiles,
                width=250,
                height=500,
            ),
            bgcolor=ft.colors.BLACK,
        )
        return self.sidebar_container


class MainContent:
    def __init__(self):
        # ft.Columnを使用して複数のコンテンツを管理
        self.display = ft.Column(
            controls=[ft.Text("地域を選択してください。", expand=True)],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def update_content(self, content, page):
        """メインエリアの内容を更新"""
        # コンテンツを完全に置き換える
        self.display.controls = content
        page.update()

    def build_main_content(self):
        """メインエリアを作成"""
        return ft.Container(content=self.display, expand=True, alignment=ft.alignment.center)

def format_datetime(datetime_str):
    """
    ISO形式の日時文字列を読みやすい形式に変換
    例: '2024-12-06T11:00:00+09:00' → '2024年12月06日'
    """
    try:
        # ISO形式の日時文字列をパース
        dt = datetime.fromisoformat(datetime_str)
        # 日付のみの形式にフォーマット
        return dt.strftime('%Y年%m月%d日')
    except (ValueError, TypeError):
        # 変換に失敗した場合は元の文字列をそのまま返す
        return datetime_str


def find_valid_weather_icon(weather_code):
    """
    指定された天気コードの画像が存在するまで、コードを1ずつ下げて探す
    
    Args:
        weather_code (str): 元の天気コード
    
    Returns:
        str: 存在する天気コードのURL
    """
    base_url = "https://www.jma.go.jp/bosai/forecast/img/"
    
    # 元のコードから始める
    current_code = weather_code
    
    # 数値が100を下回るまで試行
    while int(current_code) > 100:
        try:
            # 画像のURLを確認
            response = requests.head(f"{base_url}{current_code}.svg")
            
            # 200 OKの場合は有効な画像とみなす
            if response.status_code == 200:
                return f"{base_url}{current_code}.svg"
            
            # 画像が見つからない場合は1を引く
            current_code = str(int(current_code) - 1)
        
        except Exception as e:
            print(f"画像取得エラー: {e}")
            break
    
    # 全て失敗した場合はデフォルト画像や空文字を返す
    return ""  # または、デフォルトの画像パスを返すことも可能

def truncate_and_wrap_text(text, max_length=23):
    """文字列を一定の長さで改行する"""
    if text is None:
        text = "--"
    text = str(text)
    return '\n'.join([text[i:i + max_length] for i in range(0, len(text), max_length)])

def safe_replace_none(value, default="--"):
    """None を指定されたデフォルト値に置き換える"""
    return default if value is None else value

class WeatherView:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.view_dropdown = None
        self.date_dropdown = None
        self.current_class10_id = None

    def create_view_dropdown(self):
        return ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("3日間の天気"),
                ft.dropdown.Option("週間天気")
            ],
            value="3日間の天気"
        )

class ThreeDayWeatherView:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.all_weather_data = []
        self.date_dropdown = None
    
    def process_weather_data(self):
        """天気データの処理とall_weather_dataの作成"""
        self.all_weather_data = []  # リセット
        
        if self.weather_data:
            for record in self.weather_data:
                # 対応する降水確率データを検索
                pops_for_time = [
                    pop for pop in self.weather_pops_data 
                    if format_datetime(pop[4]) == format_datetime(record[4])
                ]
                
                # 対応する気温データを検索
                temps_for_date = [
                    temp for temp in self.weather_temps_data 
                    if format_datetime(temp[4]) == format_datetime(record[4])
                ]

                # 温度情報を抽出
                area_name = "--"
                min_temp = "--"
                max_temp = "--"

                if temps_for_date and len(temps_for_date) >= 2:
                    area_name = temps_for_date[0][6]
                    min_temp = safe_replace_none(temps_for_date[0][5])
                    max_temp = safe_replace_none(temps_for_date[1][5])
                
                # 6時間ごとの時間帯を定義
                time_ranges = [
                    {'range': '00:00~06:00', 'start': 0, 'end': 6},
                    {'range': '06:00~12:00', 'start': 6, 'end': 12},
                    {'range': '12:00~18:00', 'start': 12, 'end': 18},
                    {'range': '18:00~24:00', 'start': 18, 'end': 24}
                ]
                
                # 降水確率情報を整理
                pops_details = []
                for time_range in time_ranges:
                    matching_pops = [
                        pop for pop in pops_for_time 
                        if time_range['start'] <= datetime.fromisoformat(pop[4]).hour < time_range['end']
                    ]
                    pops = matching_pops[0][5] if matching_pops else '--'
                    pops_details.append({
                        'time_range': time_range['range'],
                        'pops': pops
                    })
                
                weather_icon_url = find_valid_weather_icon(record[5])
                self.all_weather_data.append({
                    'area_name': record[3],
                    'temp_area_name': area_name,
                    'min_temp': min_temp,
                    'max_temp': max_temp,
                    'pops_data': pops_details,
                    'publishing_office': record[1],
                    'report_datetime': record[2],
                    'time_define': record[4],
                    'formatted_time_define': format_datetime(record[4]),
                    'weather_icon_url': weather_icon_url,
                    'weather_code': record[5],
                    'weather': safe_replace_none(record[6]),
                    'wind': safe_replace_none(record[7]),
                    'wave': safe_replace_none(record[8]),
                })

    def get_weather_data_for_date(self, selected_date):
        """指定された日付の天気データを取得"""
        return next((data for data in self.all_weather_data 
                    if data['formatted_time_define'] == selected_date), None)

    def get_initial_weather_data(self):
        """初期表示用の天気データを取得"""
        return self.all_weather_data[0] if self.all_weather_data else {
            'area_name': '--',
            'temp_area_name': '--',
            'min_temp': '--',
            'max_temp': '--',
            'pops_data': [],
            'publishing_office': '--',
            'report_datetime': '--',
            'formatted_time_define': '--',
            'weather_icon_url': '',
            'weather_code': '',
            'weather': '--',
            'wind': '--',
            'wave': '--',
        }

    def fetch_weather_data(self, class10_id):
        """天気データの取得"""
        self.weather_data = self.db_manager.fetch_weather_info(class10_id)
        self.weather_pops_data = self.db_manager.fetch_weather_pops(class10_id)
        self.weather_temps_data = self.db_manager.fetch_weather_temps(class10_id)

    def create_date_dropdown(self):
        """日付選択用ドロップダウンの作成"""
        today = datetime.today().strftime('%Y年%m月%d日')
        unique_dates = sorted(set(format_datetime(record[4]) for record in self.weather_data))
        display_dates = [
            f"{date}（今日）" if date == today else date for date in unique_dates
        ]
        
        self.date_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(display_date) for display_date in display_dates],
            value=display_dates[0] if display_dates else None,
            width=300
        )
        return self.date_dropdown

    def create_weather_info_container(self, weather_data):
        """天気情報のコンテナを作成"""
        return ft.Container(
            content=ft.Column([
                ft.Text(f" {weather_data['area_name']}", weight=ft.FontWeight.BOLD, size=16, color=ft.colors.BLUE_900),
                ft.Text(f"気象台： {weather_data['publishing_office']}", weight=ft.FontWeight.BOLD),
                ft.Text(f"報告日時： {format_datetime(weather_data['report_datetime'])}", color=ft.colors.GREY_600),
            ]),
            padding=10,
            margin=5,
            border_radius=10,
            bgcolor=ft.colors.BLUE_50
        )

    def create_weather_details_container(self, weather_data):
        """天気詳細のコンテナを作成"""
        return ft.Container(
            content=ft.Column([
                self.date_dropdown,
                ft.Row([
                    ft.Image(
                        src=weather_data['weather_icon_url'],
                        width=100,
                        height=100
                    ) if weather_data['weather_icon_url'] else ft.Text("画像なし"),
                    ft.Column([
                        ft.Text(f"天気: {truncate_and_wrap_text(weather_data['weather'])}"),
                        ft.Text(f"風速: {truncate_and_wrap_text(weather_data['wind'])}"),
                        ft.Text(f"波: {truncate_and_wrap_text(weather_data['wave'])}"),
                    ])
                ])
            ]),
            padding=10,
            margin=5,
            border_radius=10,
            bgcolor=ft.colors.BLUE_100,
            border=ft.border.all(1, ft.colors.BLUE_300)
        )

    def create_pops_temps_container(self, weather_data):
        """降水確率と気温のコンテナを作成"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    self.create_pops_container(weather_data['pops_data']),
                    self.create_temps_container(weather_data)
                ]),
            ]),
            padding=10,
            margin=5,
            border_radius=10,
            bgcolor=ft.colors.WHITE,
        )

    def create_pops_container(self, pops_data):
        """降水確率のコンテナを作成"""
        return ft.Container(
            content=ft.Column([
                ft.Text("降水確率", weight=ft.FontWeight.BOLD),
                ft.Column([
                    ft.Row([
                        ft.Text(f"{pop['time_range']}", expand=True),
                        ft.Text(
                            f"{pop['pops']}%" if pop['pops'] != '--' else '--', 
                            color=ft.colors.BLUE_900 if pop['pops'] != '--' else ft.colors.GREY_600
                        )
                    ]) for pop in pops_data
                ]),
            ]),
            padding=10,
            margin=5,
            border_radius=10,
            bgcolor=ft.colors.BLUE_50,
            border=ft.border.all(1, ft.colors.BLUE_300),
            expand=True
        )

    def create_temps_container(self, weather_data):
        """気温のコンテナを作成"""
        return ft.Container(
            content=ft.Column([
                ft.Text("気温", weight=ft.FontWeight.BOLD),
                ft.Text(f"地域: {weather_data['temp_area_name']}", weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Text("最低気温:", expand=True),
                    ft.Text(
                        f"{weather_data['min_temp']}℃" if weather_data['min_temp'] != '--' else '--',
                        color=ft.colors.BLUE_900 if weather_data['min_temp'] != '--' else ft.colors.GREY_600
                    )
                ]),
                ft.Row([
                    ft.Text("最高気温:", expand=True),
                    ft.Text(
                        f"{weather_data['max_temp']}℃" if weather_data['max_temp'] != '--' else '--',
                        color=ft.colors.BLUE_900 if weather_data['max_temp'] != '--' else ft.colors.GREY_600
                    )
                ])
            ]),
            padding=10,
            margin=5,
            border_radius=10,
            bgcolor=ft.colors.BLUE_50,
            border=ft.border.all(1, ft.colors.BLUE_300),
            expand=True
        )

    def build_view(self, weather_data):
        """3日間の天気ビューを構築"""
        return ft.Column([
            self.create_weather_info_container(weather_data),
            self.create_weather_details_container(weather_data),
            self.create_pops_temps_container(weather_data)
        ])

class WeeklyWeatherView:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.weather_data = None
        self.temp_data = None
        self.averages_data = None

    def fetch_weekly_data(self, office_id, class10_id):
        """週間天気データと気温データの取得"""
        self.weather_data = self.db_manager.fetch_weather_reliabilities(office_id)
        self.temp_data = self.db_manager.fetch_weather_temps_by_name(class10_id)


    def format_temp_range(self, min_temp, min_upper, min_lower, max_temp, max_upper, max_lower):
        """気温範囲の文字列を生成"""
        min_range = f"{min_lower or '--'}～{min_upper or '--'}"
        max_range = f"{max_lower or '--'}～{max_upper or '--'}"
        return min_range, max_range

    def create_daily_weather_card(self, weather_data, temp_data):
        """1日分の天気カードを作成"""
        weather_icon_url = find_valid_weather_icon(weather_data[5])
        
        # 気温情報の整形
        min_range = "--～--"
        max_range = "--～--"
        area_name = ""
        
        if temp_data:
            min_range, max_range = self.format_temp_range(
                temp_data[5], temp_data[6], temp_data[7],  # min temps
                temp_data[8], temp_data[9], temp_data[10]  # max temps
            )
            area_name = temp_data[3]

        return ft.Container(
            content=ft.Column([
                # 日付
                ft.Text(
                    format_datetime(weather_data[4]),
                    weight=ft.FontWeight.BOLD,
                    size=16
                ),
                # 地域名
                ft.Text(
                    area_name,
                    size=14,
                    color=ft.colors.GREY_700,
                    italic=True
                ),
                # 天気アイコンと確率
                ft.Row([
                    ft.Image(
                        src=weather_icon_url,
                        width=50,
                        height=50,
                        fit=ft.ImageFit.CONTAIN
                    ) if weather_icon_url else ft.Text("画像なし"),
                    ft.Column([
                        ft.Text(f"降水確率: {weather_data[6]}%"),
                        ft.Text(f"信頼度: {weather_data[7]}")
                    ]),
                ], alignment=ft.MainAxisAlignment.CENTER),
                # 気温情報
                ft.Container(
                    content=ft.Column([
                        ft.Text("気温", weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"最低: {min_range}℃",
                            color=ft.colors.BLUE,
                            size=14
                        ),
                        ft.Text(
                            f"最高: {max_range}℃",
                            color=ft.colors.RED,
                            size=14
                        ),
                    ]),
                    padding=ft.padding.only(top=10),
                ),
            ]),
            padding=10,
            margin=5,
            border_radius=20,
            bgcolor=ft.colors.BLUE_50,
            border=ft.border.all(1, ft.colors.BLUE_300),
            width=200,
        )
        
    def load_averages_data(self, class10_id):
        """平均気温と降水確率のデータを読み込む"""
        self.temp_averages_data = self.db_manager.fetch_temp_averages(class10_id)
        self.pop_averages_data = self.db_manager.fetch_pop_averages(class10_id)

    def create_averages_card(self):
        """週間平均情報カードを作成"""
        if not self.temp_averages_data and not self.pop_averages_data:
            return None

        # 最初のレコードを取得
        temp_ave = self.temp_averages_data[0] if self.temp_averages_data else None
        pop_ave = self.pop_averages_data[0] if self.pop_averages_data else None

        # 地域名を取得（気温データまたは降水確率データから）
        area_name = "不明"
        if temp_ave and len(temp_ave) > 3:
            area_name = temp_ave[3]
        elif pop_ave and len(pop_ave) > 3:
            area_name = pop_ave[3]
        
        return ft.Container(
            content=ft.Column([
                # 地域名
                ft.Container(
                    content=ft.Text(area_name, weight=ft.FontWeight.BOLD, size=14),
                    padding=ft.padding.only(left=15, bottom=5)
                ),
                # ラベル行
                ft.Row([
                    ft.Container(
                        content=ft.Text("気温", weight=ft.FontWeight.BOLD),
                        padding=ft.padding.only(left=15)
                    ),
                    ft.Container(
                        content=ft.Text("降水確率", weight=ft.FontWeight.BOLD),
                        padding=ft.padding.only(left=15)
                    ),
                ], spacing=130),
                # 値の行
                ft.Row([
                    # 気温の平均値
                    ft.Container(
                        content=ft.Row([
                            ft.Text(
                                f"最低 {temp_ave[0] if temp_ave else '--'}℃",
                                color=ft.colors.BLUE,
                                size=16
                            ),
                            ft.Text(" / "),
                            ft.Text(
                                f"最高 {temp_ave[1] if temp_ave else '--'}℃",
                                color=ft.colors.RED,
                                size=16
                            ),
                        ]),
                        padding=15,
                        margin=10,
                        border_radius=30,
                        bgcolor=ft.colors.BLUE_50,
                        border=ft.border.all(1, ft.colors.BLUE_200)
                    ),
                    # 降水確率の平均値
                    ft.Container(
                        content=ft.Row([
                            ft.Text(
                                f"最小 {pop_ave[0] if pop_ave else '--'}%",
                                color=ft.colors.CYAN,
                                size=16
                            ),
                            ft.Text(" / "),
                            ft.Text(
                                f"最大 {pop_ave[1] if pop_ave else '--'}%",
                                color=ft.colors.INDIGO,
                                size=16
                            ),
                        ]),
                        padding=15,
                        margin=10,
                        border_radius=30,
                        bgcolor=ft.colors.BLUE_50,
                        border=ft.border.all(1, ft.colors.BLUE_200)
                    )
                ])
            ])
        )

    def build_view(self, office_id, class10_id):
        # まずデータを読み込む
        self.load_averages_data(class10_id)

        """週間天気ビューを構築"""
        self.fetch_weekly_data(office_id, class10_id)
        
        if not self.weather_data:
            return ft.Container(
                content=ft.Text("週間天気のデータがありません", color=ft.colors.RED),
                padding=10,
                margin=10,
                border_radius=10,
                bgcolor=ft.colors.GREY_200,
                border=ft.border.all(1, ft.colors.GREY_400)
            )

        # 最初のデータから地域情報を取得
        first_data = self.weather_data[0]
        header = ft.Container(
            content=ft.Column([
                ft.Text(f"{first_data[3]}", weight=ft.FontWeight.BOLD, size=16, color=ft.colors.BLUE_900),
                ft.Text(f"気象台： {first_data[1]}", weight=ft.FontWeight.BOLD),
                ft.Text(f"報告日時： {format_datetime(first_data[2])}", color=ft.colors.GREY_600),
            ]),
            padding=10,
            margin=5,
            border_radius=10,
            bgcolor=ft.colors.BLUE_50
        )

        # 日付ごとのデータをグループ化
        daily_data = {}
        for weather in self.weather_data:
            date = format_datetime(weather[4])
            if date not in daily_data:
                daily_data[date] = {'weather': weather, 'temp': None}

        # 気温データを日付ごとのデータに追加
        for temp in self.temp_data:
            date = format_datetime(temp[4])
            if date in daily_data:
                daily_data[date]['temp'] = temp

        # 天気カードを横スクロール可能なコンテナに配置
        weather_cards = ft.Row(
            [self.create_daily_weather_card(
                data['weather'], 
                data['temp']
            ) for data in daily_data.values()],
            scroll=ft.ScrollMode.AUTO,
            auto_scroll=True
        )

        return ft.Column([
            header,
            ft.Container(
                content=weather_cards,
                padding=10,
                margin=5,
                bgcolor=ft.colors.WHITE,
            ),
            self.create_averages_card()  # 平均値カードを追加
        ])


def display_selected_region(center_id, office_id, class10_id, db_manager, main_content, page, sidebar=None):
    try:
        # ビューの初期化
        weather_view = WeatherView(db_manager)
        three_day_view = ThreeDayWeatherView(db_manager)
        weekly_view = WeeklyWeatherView(db_manager)

        # ビュー選択用ドロップダウンの作成
        view_dropdown = weather_view.create_view_dropdown()
        view_dropdown.disabled = False

        def on_view_change(e):
            if view_dropdown.disabled:
                return

            try:
                view_dropdown.disabled = True
                page.update()

                if e.control.value == "週間天気":
                    weekly_content = weekly_view.build_view(office_id, class10_id)
                    main_content.update_content([
                        ft.Column([
                            view_dropdown,
                            weekly_content
                        ])
                    ], page)
                else:
                    display_three_day_weather()

            finally:
                view_dropdown.disabled = False
                page.update()

        view_dropdown.on_change = on_view_change

        def display_three_day_weather():
            three_day_view.fetch_weather_data(class10_id)
            
            if three_day_view.weather_data:
                three_day_view.process_weather_data()
                date_dropdown = three_day_view.create_date_dropdown()
                date_dropdown.disabled = False

                def on_date_change(e):
                    if date_dropdown.disabled:
                        return

                    try:
                        date_dropdown.disabled = True
                        page.update()

                        selected_date = e.control.value.replace("（今日）", "")
                        weather_data = three_day_view.get_weather_data_for_date(selected_date)
                        if weather_data:
                            main_content.update_content([
                                ft.Column([
                                    view_dropdown,
                                    three_day_view.build_view(weather_data)
                                ])
                            ], page)

                    finally:
                        date_dropdown.disabled = False
                        page.update()

                date_dropdown.on_change = on_date_change

                initial_data = three_day_view.get_initial_weather_data()
                main_content.update_content([
                    ft.Column([
                        view_dropdown,
                        three_day_view.build_view(initial_data)
                    ])
                ], page)
            else:
                no_data_container = ft.Container(
                    content=ft.Text("該当する天気情報はありません。", color=ft.colors.RED),
                    padding=10,
                    margin=10,
                    border_radius=10,
                    bgcolor=ft.colors.GREY_200,
                    border=ft.border.all(1, ft.colors.GREY_400)
                )
                main_content.update_content([
                    ft.Column([
                        view_dropdown,
                        no_data_container
                    ])
                ], page)

        # 初期表示
        display_three_day_weather()

    finally:
        if sidebar:
            sidebar.set_processing_state(False)


def update_main_content(selected_display_date, unique_dates, all_weather_data, main_content, weather_dropdown, page):
    # 選択された日付に対応するデータを検索
    selected_data = next(
        (data for data in all_weather_data if data['formatted_time_define'] == selected_display_date), 
        None
    )

    if selected_data:
        # 降水確率の詳細を別の四角形にまとめる
        pops_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    # 降水確率のコンテナ
                    ft.Container(
                        content=ft.Column([
                            ft.Text("降水確率", weight=ft.FontWeight.BOLD),
                            ft.Column([
                                ft.Row([
                                    ft.Text(f"{pop['time_range']}", expand=True),
                                    ft.Text(f"{pop['pops']}%" if pop['pops'] != '--' else '--', 
                                            color=ft.colors.BLUE_900 if pop['pops'] != '--' else ft.colors.GREY_600)
                                ]) for pop in selected_data['pops_data']
                            ]),
                        ]),
                        padding=10,
                        margin=5,
                        border_radius=10,
                        bgcolor=ft.colors.BLUE_50,
                        border=ft.border.all(1, ft.colors.BLUE_300),
                        expand=True
                    ),
                    # 気温情報のコンテナ
                    ft.Container(
                        content=ft.Column([
                            ft.Text("気温", weight=ft.FontWeight.BOLD),
                            ft.Text(f"地域: {selected_data['temp_area_name']}", weight=ft.FontWeight.BOLD),
                            ft.Row([
                                ft.Text("最低気温:", expand=True),
                                ft.Text(f"{selected_data['min_temp']}℃" if selected_data['min_temp'] != '--' else '--', 
                                        color=ft.colors.BLUE_900 if selected_data['min_temp'] != '--' else ft.colors.GREY_600)
                            ]),
                            ft.Row([
                                ft.Text("最高気温:", expand=True),
                                ft.Text(f"{selected_data['max_temp']}℃" if selected_data['max_temp'] != '--' else '--', 
                                        color=ft.colors.BLUE_900 if selected_data['max_temp'] != '--' else ft.colors.GREY_600)
                            ])
                        ]),
                        padding=10,
                        margin=5,
                        border_radius=10,
                        bgcolor=ft.colors.BLUE_50,
                        border=ft.border.all(1, ft.colors.BLUE_300),
                        expand=True
                    ),
                ]),
            ]),
            padding=10,
            margin=5,
            border_radius=10,
            bgcolor=ft.colors.WHITE,
        )

        selected_data_container = ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text(f" {selected_data['area_name']}", weight=ft.FontWeight.BOLD, size=16, color=ft.colors.BLUE_900),
                    ft.Text(f"気象台： {selected_data['publishing_office']}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"報告日時： {format_datetime(selected_data['report_datetime'])}", color=ft.colors.GREY_600),
                ]),
                padding=10,
                margin=5,
                border_radius=10,
                bgcolor=ft.colors.BLUE_50
            ),
            ft.Container(
                content=ft.Column([
                    weather_dropdown,  # ドロップダウンを保持
                    ft.Row([
                        # 天気アイコン
                        ft.Image(
                            src=selected_data['weather_icon_url'],
                            width=100,
                            height=100
                        ) if selected_data['weather_icon_url'] else ft.Text("画像なし"),
                        ft.Column([
                            ft.Text(f"天気: {truncate_and_wrap_text(selected_data['weather'])}"),
                            ft.Text(f"風速: {truncate_and_wrap_text(selected_data['wind'])}"),
                            ft.Text(f"波: {truncate_and_wrap_text(selected_data['wave'])}"),
                        ])
                    ])
                ]),
                padding=10,
                margin=5,
                border_radius=10,
                bgcolor=ft.colors.BLUE_100,
                border=ft.border.all(1, ft.colors.BLUE_300)
            ),
            pops_container
        ])
        
        # メインコンテンツを更新
        main_content.update_content([selected_data_container], page)
    else:
        no_data_container = ft.Container(
            content=ft.Text("選択した日付の天気情報はありません。", color=ft.colors.RED),
            padding=10,
            margin=10,
            border_radius=10,
            bgcolor=ft.colors.GREY_200,
            border=ft.border.all(1, ft.colors.GREY_400)
        )
        main_content.update_content([no_data_container], page)

def update_database():
    """データベースを再作成する関数"""
    db_path = "region_data.db"
    try:
        # 既存のデータベースを削除
        if os.path.exists(db_path):
            os.remove(db_path)
            print("既存のデータベースを削除しました。")
        
        # データベースを再作成
        return ensure_database_exists()
    except Exception as e:
        print(f"データベース更新中にエラーが発生しました: {e}")
        return False



def main(page: ft.Page):
    if not ensure_database_exists():
        print("データベースの準備に失敗しました。アプリケーションを終了します。")
        sys.exit(1)

    page.title = "天気予報アプリ"
    
    # プログレスリング用のコンテナを作成
    progress_container = ft.Container(
        visible=False,
        content=ft.ProgressRing(),
        alignment=ft.alignment.center,
    )



    def update_button_clicked(e):
        print("更新ボタンがクリックされました")  # デバッグ用

        # 画面を白紙に戻す
        page.clean()
        
    # 更新中の表示
        loading_display = ft.Container(
            content=ft.Column(
                controls=[
                    # 上部に空のコンテナを追加して下げる
                    ft.Container(height=100),  # この値を調整して位置を制御できます
                    ft.ProgressRing(),
                    ft.Text("データベースを更新中です...", size=20)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )
        
        page.add(loading_display)
        page.update()


        try:
            # データベースを更新
            if update_database():
                print("データベースの更新が完了しました")
                page.clean()
                create_title_bar()
                initialize_main_view()
            else:
                print("データベースの更新に失敗しました")
                # エラーメッセージを表示
                page.clean()
                page.add(ft.Text("更新に失敗しました。", color=ft.colors.RED))
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
            page.clean()
            page.add(ft.Text(f"エラーが発生しました: {str(e)}", color=ft.colors.RED))

    # タイトルバーを作成する関数
    def create_title_bar():
        page.add(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            "気象情報アプリ",
                            size=30,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.WHITE
                        ),
                        ft.IconButton(
                            icon=ft.icons.REFRESH,
                            icon_color=ft.colors.WHITE,
                            tooltip="データベースを更新",
                            on_click=update_button_clicked
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center,
                bgcolor=ft.colors.BLUE,
                padding=10
            )
        )
        # プログレスリングのコンテナを追加
        page.add(progress_container)


    # メインの画面を初期化する関数
    def initialize_main_view():
        page.scroll = ft.ScrollMode.AUTO
        page.horizontal_alignment = ft.CrossAxisAlignment.START

        db_manager = DatabaseManager()

        # 地域データの取得
        region_data = db_manager.fetch_region_hierarchy()

        # 地域データが空の場合の処理
        if not region_data:
            page.add(ft.Text("データベースに地域データがありません。"))
            return

        # メインコンテンツエリアの初期化
        main_content = MainContent()

        # サイドバーの初期化
        sidebar = Sidebar(
            region_data=region_data,
            on_selection_change=lambda center_id, office_id, class10_id, sb: 
                display_selected_region(center_id, office_id, class10_id, db_manager, main_content, page, sb)
        )

        # サイドバーとメインコンテンツの配置
        page.add(
            ft.Row(
                [sidebar.build_sidebar(), main_content.build_main_content()],
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
            )
        )

    # 初期画面の表示
    create_title_bar()
    initialize_main_view()
    page.update()

# Fletアプリケーションを開始
ft.app(target=main)