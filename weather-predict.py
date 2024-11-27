import requests
import json
import flet as ft

# 地域情報のURL
URL = "http://www.jma.go.jp/bosai/common/const/area.json"

# JSONデータを取得
response = requests.get(URL)

# GUIアプリケーションを構築
def main(page: ft.Page):
    page.title = "地方と場所のタブ"
    page.scroll = ft.ScrollMode.AUTO
    
    # データ取得が成功した場合
    if response.status_code == 200:
        data_json = response.json()  # JSON形式でデータを取得
        centers = data_json.get("centers", {})

        # 地方ごとのタブを作成
        regional_tabs = []
        for region_id, region_info in centers.items():
            # 地方名を取得（nameが文字化けの場合があるため確認）
            region_name = region_info.get("name", "不明な地方")
            
            # 地方内の子の場所タブを作成
            child_tabs = []
            for child_id in region_info.get("children", []):
                child_name = data_json.get("offices", {}).get(child_id, {}).get("name", "不明な場所")
                child_tabs.append(
                    ft.Tab(
                        text=child_name,
                        content=ft.Text(f"地域ID: {child_id}\n地域名: {child_name}")
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
