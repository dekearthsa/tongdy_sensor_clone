import sqlite3
PATH_DB = "/Users/pcsishun/project_envalic/hlr_control_system/hlr_backend/hlr_db.db"
conn = sqlite3.connect(PATH_DB)

cursor = conn.cursor()

data =cursor.execute("""
    SELECT * FROM state_hlr
    """).fetchall()


data2 =cursor.execute("""
    SELECT * FROM setting_control
    """).fetchall()

print(data, "\n")



print(data2)
