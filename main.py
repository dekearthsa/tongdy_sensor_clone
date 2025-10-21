from queue import Queue
# from mock_sensor_poller import create_mock_poller
from sensor_poller import SensorPoller
import time
import sqlite3
import threading
import requests
# from datetime import datetime

PATH_DB = "/Users/pcsishun/project_envalic/hlr_control_system/hlr_backend/hlr_db.db"
CTRL_URL = "http://172.29.247.180" # /emergency_shutdown GET  # 405 
# SESSION = requests.Session()
# conn = sqlite3.connect(PATH_DB)
# cursor = conn.cursor()

## connect db 
def open_conn():
    conn = sqlite3.connect(PATH_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    return conn

## curd db ## 
def get_setting_control(conn, cyclic_name: str):
    sql = """SELECT * FROM setting_control WHERE cyclic_name = ? LIMIT 1"""
    cur = conn.cursor()
    cur.execute(sql, (cyclic_name,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Not found cyclic: {cyclic_name}")
    return row  # sqlite3.Row => เข้าถึงด้วย row['regen_fan_volt'] ได้

def update_endtime_and_state(conn, new_startime: int, new_endtime_ms: int, new_state: str):
    sql = """
        UPDATE state_hlr
        SET starttime =?, endtime = ?, systemState = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (new_startime ,new_endtime_ms, new_state))
    conn.commit()

def update_state_active(conn):
    sql = """
        UPDATE state_hlr
        SET is_start = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (False,))
    conn.commit()

def update_state_cyclicloop(conn, loop_count:int):
    sql = """
        UPDATE state_hlr
        SET cyclic_loop_dur = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (loop_count,))
    conn.commit()

def handle_end_loop():
    status = requests.get(CTRL_URL + '/stop')
    print(f"{status.status_code} END..")


## send function auto
def send_payload_control(conn,state, heater, fanvolt, duration_ms):
    print("start send payload...")
    payload = {
        "phase": state,        # string: "REGEN", "COOLDOWN", "IDLE", "SCRUB"
        "fan_volt": fanvolt,   # float
        "heater": heater,      # bool
        "duration": duration_ms # int (milliseconds)
    }

    print(CTRL_URL + "/auto")
    print(f"debug send => {payload}")

    status = requests.post(
        CTRL_URL + "/auto",
        json=payload,      
        timeout=3
    )

    print("status code:", status.status_code)
    print("response:", status.text)
    # status = SESSION.post(CTRL_URL+"/auto", data=payload, headers=headers, timeout=3). abcDEF99
    print("status => ",status.status_code)
    print("status => ",status)
    if status.status_code == 405:
            for i in range(4):
                if i < 5:
                    print(f"try to send command {i+1}/5")
                    status = requests.post(
                        CTRL_URL + "/auto",
                        json=payload,      
                        timeout=3
                    )
                    if status.status_code == 200:
                        break
                    else:
                        time.sleep(1)
                else:
                    print("Force stop emergency shutdown")
                    update_endtime_and_state(conn, 0,0, "end")
                    update_state_active(conn)
                    status = requests.get(CTRL_URL+"/emergency_shutdown",timeout=3)
                    print(status)
                    break
                    

    # except Exception as e:
    #     print(f"[control] error: {e}")


### Checking loop thread
def checking_state_loop(stop_event: threading.Event, sleep_sec: float = 1.0):
    print("Started thread")
    conn = open_conn()
    # try:
    while not stop_event.is_set():
            # print("Thread running...")
            el = conn.execute("SELECT * FROM state_hlr").fetchone()
            # print("conn => ", el['is_start'])
            if  el['is_start'] == 0: 
                # print("system off")
                continue 

            # row_id = el["id"]
            cyclic_name = el["cyclicName"]
            # print("cyclic_name => ", cyclic_name, el["cyclicName"])
            system_state = el["systemState"]
            # print("system_state => ", system_state, el["systemState"])
            endtime_ms = el["endtime"] ## ms
            # print("endtime_ms => ", endtime_ms, el["endtime"])
            cyc_loop = int(el['cyclic_loop_dur'])
            # print("cyc_loop => ", cyc_loop, int(el['cyclic_loop_dur']))
            if cyc_loop <= 0:
                print("in condition cyc_loop = 0", cyc_loop)
                handle_end_loop()
                update_endtime_and_state(conn, 0,0, "end")
                update_state_active(conn)
                continue
            
            try:
                setting = get_setting_control(conn, cyclic_name)
                # print("setting => ",setting)
            except Exception as e:
                print("error in get_setting_control")
                print(f"[checking] {e}")
                continue
            starttime =  int(time.time() * 1000)
            # ดึงค่าจาก setting_control
            regen_fan_volt = setting["regen_fan_volt"]
            # print("regen_fan_volt => ",regen_fan_volt)
            # regen_duration = int(setting["regen_duration"] * 60 * 1000) # ms
            regen_duration = int(setting["regen_duration"]) # min
            # print("regen_duration => ",regen_duration)
            # regen_duration = int(setting["regen_duration"]* 60 * 1000)
            cool_fan_volt = setting["cool_fan"]
            # print("cool_fan_volt => ",cool_fan_volt)
            # cool_duration = int(setting["cool_duration"]* 60 * 1000) # ms
            cool_duration = int(setting["cool_duration"])  # min
            # print("cool_duration => ",cool_duration)
            # idle_duration = int(setting["idle_duration"] * 60* 1000) # ms
            idle_duration = int(setting["idle_duration"]) # min
            # print("idle_duration => ",idle_duration)
            scab_fan_volt = setting["scab_fan_volt"]
            # print("scab_fan_volt => ",scab_fan_volt)
            # scab_duration = int(setting["scab_duration"]* 60 * 1000) # ms
            scab_duration = int(setting["scab_duration"] ) # min
            # print("scab_duration => ",scab_duration)
            # cyc_loop = int(setting['cyclic_loop'])
            # print("regen_fan_volt => ", regen_fan_volt)
            if system_state == "regen_firsttime":
                print("in condition regen_firsttime")
                send_payload_control(conn,"regen", True, regen_fan_volt, regen_duration)
                # update_endtime_and_state(conn, row_id, now_ms + cool_duration, "COOLDOWN")
                update_endtime_and_state(conn, 
                                        starttime,
                                        starttime + (regen_duration * 60 *1000) , 
                                        "cooldown") 
                continue

            if  starttime  >= endtime_ms and endtime_ms > 0:
                
                if system_state == "regen":
                    print("in condition regen")
                    send_payload_control(conn,"regen", True, regen_fan_volt, regen_duration)
                    # update_endtime_and_state(conn, row_id, now_ms + cool_duration, "COOLDOWN")
                    update_endtime_and_state(conn, 
                                            starttime,
                                            starttime + (regen_duration * 60 *1000) , 
                                            "cooldown") 
                    continue

                if system_state == "cooldown":
                    print("in condition cooldown")
                    send_payload_control(conn,"cooldown", False, cool_fan_volt, cool_duration)
                    # update_endtime_and_state(conn, row_id, now_ms + idle_duration, "IDLE")
                    update_endtime_and_state(conn, 
                                             starttime, 
                                             starttime + (cool_duration * 60 *1000) ,
                                             "idle")
                    continue

                elif system_state == "idle":
                    print("in condition idle")
                    send_payload_control(conn,"idle", False, 0, idle_duration)
                    # update_endtime_and_state(conn, row_id, now_ms + scab_duration, "SCRUB")
                    update_endtime_and_state(conn, 
                                             starttime, 
                                             starttime + (idle_duration * 60 *1000) ,
                                             "scrub")
                    continue

                elif system_state == "scrub":
                    print("in condition scrub")
                    send_payload_control(conn,"scrub", False, scab_fan_volt, scab_duration)  
                    update_state_cyclicloop(conn, cyc_loop-1)
                    update_endtime_and_state(conn, starttime,starttime + (scab_duration* 60 * 1000), "regen")
                    # if cyc_loop <= 0:
                    #     print("in condition cyc_loop = 0", cyc_loop)
                    #     update_endtime_and_state(conn, 0,0, "end")
                    #     update_state_active(conn)
                    #     continue
                    # else: 
                    #     print("in else cyc_loop ", cyc_loop)
                    #     update_endtime_and_state(conn, 
                    #                              starttime,
                    #                              starttime + (scab_duration* 60 * 1000), 
                    #                              "regen")
                    #     continue 


            stop_event.wait(sleep_sec)
    # except Exception as e:
    #     print(f"[checking_loop] fatal: {e}")
    # finally:
    #     conn.close()

def start_checking_thread():
    print("Starting thread....")
    stop_event = threading.Event()
    t = threading.Thread(target=checking_state_loop, args=(stop_event,), daemon=True)
    t.start()
    return stop_event, t

def save_to_db(now_ms, sensor_id, co2, temp, humid, mode, sensor_type):
    try:
        conn = open_conn()
        cur = conn.cursor()
        # now_ms = int(time.time() * 1000) 
        cur.execute("""
            INSERT INTO hlr_sensor_data (datetime, sensor_id, co2, temperature, humidity, mode, sensor_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now_ms, sensor_id, co2, temp, humid, mode, sensor_type))
        conn.commit()
        print("Saved")
    except Exception as err:
        print(f"error when save in database {err}")

def main():
    print("start.... main try to get queue")
    set_queue = Queue()
    poller = SensorPoller(
        ui_queue=set_queue,
        polling_interval=10
    )
    poller.start()
    time.sleep(10)
    poller.stop()

    while not set_queue.empty():
        
        data_sensor = set_queue.get()
        # print("data_sensor => ", data_sensor)
        data = data_sensor['data']
        now_ms = int(time.time() * 1000) 
        # print("data => ",data)
        # print("start.... main")
        # print("sensor_id => ", data['sensor_id'])
        # print("co2 => ", data['co2'])
        # print("temperature => ", data['temperature'])
        # print("humidity => ", data['humidity'])
        # print("sensor_type => ", data['sensor_type'])
        if data['sensor_id'] == 51:
            save_to_db(now_ms=now_ms,
                    sensor_id= data['sensor_id'],
                    co2= data['co2'],
                    temp= data['temperature'], 
                    humid= data['humidity'], 
                    mode="test", 
                    sensor_type= "type_k")
        else:
            save_to_db(now_ms=now_ms,
                    sensor_id= data['sensor_id'],
                    co2= data['co2'],
                    temp= data['temperature'], 
                    humid= data['humidity'], 
                    mode="test", 
                    sensor_type= "tongdy")
        # print("\n")
    
    time.sleep(5)


if __name__ == "__main__":
    print("Started")
    stop_event, t = start_checking_thread()
    try:
        while True:
            main() 
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        t.join(timeout=3)