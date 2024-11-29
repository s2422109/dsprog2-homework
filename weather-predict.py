import requests
import json
import flet as ft

# 地域情報のURL
URL = "http://www.jma.go.jp/bosai/common/const/area.json"

# JSONデータを取得
response = requests.get(URL)

# GUIアプリケーションを構築
def main(page: ft.Page):
    page.title = "地域タブの階層表示"
    page.scroll = ft.ScrollMode.AUTO
    
    # データ取得が成功した場合
    if response.status_code == 200:
        data_json = response.json()  # JSON形式でデータを取得
        centers = data_json.get("centers", {})
        class15s = data_json.get("class15s", {})  # class15sを取得
        class20s = data_json.get("class20s", {})  # class20sを取得
        
        # 地域ごとのタブを作成
        regional_tabs = []
        for region_id, region_info in centers.items():
            # 地方名を取得（nameが文字化けの場合があるため確認）
            region_name = region_info.get("name", "不明な地方")
            
            # 中間区分（1の位）があるか確認し、タブを階層化
            child_tabs = []
            for child_id in region_info.get("children", []):
                # オフィス情報を取得して名前を取得
                child_info = data_json.get("offices", {}).get(child_id, {})
                child_name = child_info.get("name", "不明な場所")
                
                # さらに子がいる場合、その場所に属するタブを作成
                sub_tabs = []
                sub_region_data = child_info.get("children", [])
                for sub_child_id in sub_region_data:
                    sub_child_info = data_json.get("class10s", {}).get(sub_child_id, {})
                    sub_child_name = sub_child_info.get("name", "不明な場所")
                    
                    # 次の階層が存在する場合、その場所に属するタブを作成
                    sub_sub_tabs = []
                    sub_class15_data = sub_child_info.get("children", [])
                    for sub_class15_id in sub_class15_data:
                        sub_class15_info = class15s.get(sub_class15_id, {})
                        sub_class15_name = sub_class15_info.get("name", "不明な場所")
                        
                        # class15s の子IDはclass20s内にあるので、class20s内から情報を取得
                        sub_class20_data = sub_class15_info.get("children", [])
                        sub_class20_tabs = []
                        for sub_class20_id in sub_class20_data:
                            sub_class20_info = class20s.get(sub_class20_id, {})
                            sub_class20_name = sub_class20_info.get("name", "不明な場所")
                            
                            # class20sのタブを追加
                            sub_class20_tabs.append(
                                ft.Tab(
                                    text=sub_class20_name,
                                    content=ft.Text(f"地域ID: {sub_class20_id}\n地域名: {sub_class20_name}")
                                )
                            )
                        
                        # class20s のタブをclass15sに追加
                        sub_sub_tabs.append(
                            ft.Tab(
                                text=sub_class15_name,
                                content=ft.Tabs(
                                    tabs=sub_class20_tabs,
                                    scrollable=True
                                )
                            )
                        )
                    
                    # class15s のタブをサブタブに追加
                    sub_tabs.append(
                        ft.Tab(
                            text=sub_child_name,
                            content=ft.Tabs(
                                tabs=sub_sub_tabs,
                                scrollable=True
                            )
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
    else:
        page.add(ft.Text(f"データ取得エラー: {response.status_code}"))

# Fletアプリを開始
ft.app(target=main)
