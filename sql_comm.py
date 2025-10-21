import sqlite3
PATH_DB = "/Users/pcsishun/project_envalic/hlr_control_system/hlr_backend/hlr_db.db"
conn = sqlite3.connect(PATH_DB)

cursor = conn.cursor()

cursor.execute("""
    DROP TABLE hlr_sensor_data
    """)

