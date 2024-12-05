import sqlite3

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def fetch_region_hierarchy(self):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM areas")
        rows = cursor.fetchall()
        connection.close()

        # 結果を格納するリスト
        region_data = []
        
        for row in rows:
            # 各階層のデータを取得
            _, center_name, center_id, office_name, office_id, class10_name, class10_id = row
            region_data.append({
                "centers_name": center_name,
                "centers_id": center_id,
                "offices_name": office_name,
                "offices_id": office_id,
                "class10s_name": class10_name,
                "class10s_id": class10_id
            })

        return region_data
