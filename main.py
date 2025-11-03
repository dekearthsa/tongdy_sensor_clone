from queue import Queue, Empty
# from mock_sensor_poller import create_mock_poller
from sensor_poller import SensorPoller
import time
import sqlite3
import threading
import requests

PATH_DB = "/home/pi/hlr_backend_control/hlr_db.db"
CTRL_URL = "http://172.29.247.180"  # /emergency_shutdown GET  # 405

# ─────────────────────────────────────────────────────────────
# DB helpers
# ─────────────────────────────────────────────────────────────
def open_conn():
    conn = sqlite3.connect(PATH_DB, check_same_thread=False, timeout=5)
    conn.row_factory = sqlite3.Row
    try:
        # ใช้ WAL + กำหนด busy_timeout ลดโอกาส locked
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
    except Exception:
        pass
    return conn

def get_setting_control(conn, cyclic_name: str):
    sql = """SELECT * FROM setting_control WHERE cyclic_name = ? LIMIT 1"""
    cur = conn.cursor()
    cur.execute(sql, (cyclic_name,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Not found cyclic: {cyclic_name}")
    return row

# หมายเหตุ: ฟังก์ชันอัปเดตด้านล่างยังไม่มี WHERE
# ถ้าตาราง state_hlr มีหลายแถว ควรเพิ่ม WHERE ให้เจาะจงแถว
def update_endtime_and_state(conn, new_startime: int, new_endtime_ms: int, new_state: str):
    sql = """
        UPDATE state_hlr
        SET starttime = ?, endtime = ?, systemState = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (new_startime, new_endtime_ms, new_state))
    conn.commit()

def update_state_active(conn, active: bool = False):
    sql = """
        UPDATE state_hlr
        SET is_start = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (1 if active else 0,))
    conn.commit()

def update_state_cyclicloop(conn, loop_count: int):
    sql = """
        UPDATE state_hlr
        SET cyclic_loop_dur = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (loop_count,))
    conn.commit()

# ─────────────────────────────────────────────────────────────
# Control helpers
# ─────────────────────────────────────────────────────────────
def handle_end_loop(session: requests.Session):
    try:
        status = session.get(CTRL_URL + '/stop', timeout=3)
        print(f"{status.status_code} END..")
    except requests.RequestException as e:
        print(f"[stop] error: {e}")

def send_payload_control(conn, session: requests.Session, state, heater, fanvolt, duration_min) -> bool:
    """ส่งคำสั่งไปคอนโทรลเลอร์; สำเร็จคืน True, ล้มเหลวครบ 5 ครั้ง → ปิดระบบ + emergency แล้วคืน False"""
    payload = {
        "phase": state,        # "regen" | "cooldown" | "idle" | "scrub"
        "fan_volt": fanvolt,   # float
        "heater": heater,      # bool
        "duration": duration_min  # หน่วยเป็น "นาที"
    }

    for attempt in range(5):
        try:
            r = session.post(CTRL_URL + "/auto", json=payload, timeout=3)
            if r.status_code == 200:
                return True
            print(f"[control] attempt {attempt+1}/5: HTTP {r.status_code} → retry")
            time.sleep(1)
        except requests.RequestException as e:
            print(f"[control] attempt {attempt+1}/5: {e}")
            time.sleep(1)

    # ล้มเหลวครบ 5 ครั้ง → ปิดระบบ + emergency
    update_endtime_and_state(conn, 0, 0, "end")
    update_state_active(conn, active=False)
    try:
        session.get(CTRL_URL + "/emergency_shutdown", timeout=3)
    except requests.RequestException as e:
        print(f"[control] emergency failed: {e}")
    return False

# ─────────────────────────────────────────────────────────────
# Checking loop (run inside watchdog)
# ─────────────────────────────────────────────────────────────
def checking_state_loop(stop_event: threading.Event, heartbeat: dict, sleep_sec: float = 1.0):
    print("Started checking thread")
    session = requests.Session()
    conn = open_conn()
    try:
        while not stop_event.is_set():
            try:
                el = conn.execute("SELECT * FROM state_hlr").fetchone()
                if not el:
                    # ไม่มี state แถวใดเลย → พักแล้ววนใหม่
                    stop_event.wait(1.0)
                    heartbeat['ts'] = time.monotonic()
                    continue

                if el['is_start'] == 0:
                    # ระบบปิดอยู่ → อย่าวนลูปรัว
                    stop_event.wait(1.0)
                    heartbeat['ts'] = time.monotonic()
                    continue

                starttime   = int(time.time() * 1000)
                cyclic_name = el["cyclicName"]
                system_state = el["systemState"]
                endtime_ms  = el["endtime"]    # ms
                cyc_loop    = int(el['cyclic_loop_dur'])

                # จบลูปทั้งหมดเมื่อครบและหมดเวลา
                if cyc_loop <= 0 and starttime >= endtime_ms:
                    handle_end_loop(session)
                    update_endtime_and_state(conn, 0, 0, "end")
                    update_state_active(conn, active=False)
                    stop_event.wait(0.5)
                    heartbeat['ts'] = time.monotonic()
                    continue

                # โหลด setting ของรอบนี้
                try:
                    setting = get_setting_control(conn, cyclic_name)
                except Exception as e:
                    print(f"[checking] get_setting_control: {e}")
                    stop_event.wait(0.5)
                    heartbeat['ts'] = time.monotonic()
                    continue

                # ดึงค่าจาก setting_control
                regen_fan_volt = setting["regen_fan_volt"]
                regen_duration = int(setting["regen_duration"])  # นาที
                cool_fan_volt  = setting["cool_fan"]
                cool_duration  = int(setting["cool_duration"])   # นาที
                idle_duration  = int(setting["idle_duration"])   # นาที
                scab_fan_volt  = setting["scab_fan_volt"]
                scab_duration  = int(setting["scab_duration"])   # นาที

                # เข้าระยะแรกสุดของลูป
                if system_state == "regen_firsttime":
                    print("in condition regen_firsttime")
                    ok = send_payload_control(conn, session, "regen", True, regen_fan_volt, regen_duration)
                    if ok:
                        update_endtime_and_state(conn, starttime, starttime + regen_duration*60*1000, "cooldown")
                    stop_event.wait(0.2)
                    heartbeat['ts'] = time.monotonic()
                    continue

                # ครบระยะเวลา → สลับ state
                if starttime >= endtime_ms and endtime_ms > 0:

                    if system_state == "regen":
                        ok = send_payload_control(conn, session, "regen", True, regen_fan_volt, regen_duration)
                        if ok:
                            update_endtime_and_state(conn, starttime, starttime + regen_duration*60*1000, "cooldown")
                        stop_event.wait(0.2)
                        heartbeat['ts'] = time.monotonic()
                        continue

                    if system_state == "cooldown":
                        ok = send_payload_control(conn, session, "cooldown", False, cool_fan_volt, cool_duration)
                        if ok:
                            update_endtime_and_state(conn, starttime, starttime + cool_duration*60*1000, "idle")
                        stop_event.wait(0.2)
                        heartbeat['ts'] = time.monotonic()
                        continue

                    if system_state == "idle":
                        ok = send_payload_control(conn, session, "idle", False, 0, idle_duration)
                        if ok:
                            update_endtime_and_state(conn, starttime, starttime + idle_duration*60*1000, "scrub")
                        stop_event.wait(0.2)
                        heartbeat['ts'] = time.monotonic()
                        continue

                    if system_state == "scrub":
                        ok = send_payload_control(conn, session, "scrub", False, scab_fan_volt, scab_duration)
                        if ok:
                            update_state_cyclicloop(conn, cyc_loop - 1)
                            update_endtime_and_state(conn, starttime, starttime + scab_duration*60*1000, "regen")
                        stop_event.wait(0.2)
                        heartbeat['ts'] = time.monotonic()
                        continue

                # รอบปกติ พักตามคาบ
                stop_event.wait(sleep_sec)
                heartbeat['ts'] = time.monotonic()

            except sqlite3.OperationalError as e:
                print(f"[checking] sqlite op error: {e} → reopen")
                try:
                    conn.close()
                except Exception:
                    pass
                stop_event.wait(0.5)
                conn = open_conn()
                heartbeat['ts'] = time.monotonic()

            except requests.RequestException as e:
                print(f"[checking] HTTP error: {e}")
                stop_event.wait(1.0)
                heartbeat['ts'] = time.monotonic()

            except Exception as e:
                # กันไม่ให้เธรดหลุด
                print(f"[checking] unexpected: {e}")
                stop_event.wait(1.0)
                heartbeat['ts'] = time.monotonic()
    finally:
        try:
            conn.close()
        except Exception:
            pass
        try:
            session.close()
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────
# Watchdog/heartbeat supervisor
# ─────────────────────────────────────────────────────────────
def start_checking_thread():
    print("Starting thread....")
    service_stop = threading.Event()
    heartbeat = {'ts': time.monotonic()}

    def supervisor():
        # สร้าง/ดูแลเธรดลูก และรีสตาร์ทเมื่อ "ตาย" หรือ "ค้าง"
        th_stop = threading.Event()
        while not service_stop.is_set():
            t = threading.Thread(target=checking_state_loop, args=(th_stop, heartbeat, 1.0), daemon=True)
            t.start()

            while not service_stop.is_set():
                if not t.is_alive():
                    # เธรดลูกตายด้วย exception → ออกจากลูปเพื่อสตาร์ตใหม่
                    print("[watchdog] checking thread crashed → restart")
                    break

                # ถ้า heartbeat ไม่ขยับเกิน 15 วินาที → ถือว่าค้าง
                if time.monotonic() - heartbeat['ts'] > 15:
                    print("[watchdog] hung detected → restarting")
                    th_stop.set()
                    t.join(timeout=3)
                    break

                # ตรวจทุก 1 วินาที
                service_stop.wait(1.0)

            # เตรียมรอบใหม่ (ถ้า service ยังไม่ปิด)
            if not service_stop.is_set():
                th_stop = threading.Event()

    supervisor_thread = threading.Thread(target=supervisor, daemon=True)
    supervisor_thread.start()
    return service_stop, supervisor_thread

# ─────────────────────────────────────────────────────────────
# Data ingestion
# ─────────────────────────────────────────────────────────────
def save_to_db(now_ms, sensor_id, co2, temp, humid, mode, sensor_type):
    try:
        conn = open_conn()
        cur = conn.cursor()
        el = conn.execute("SELECT * FROM state_hlr").fetchone()
        cyclicName = "None"
        if el and el['is_start'] == 1:
            cyclicName = el["cyclicName"]
        elif el and el["systemType"] == "manual":
            cyclicName = el["systemType"]

        cur.execute("""
            INSERT INTO hlr_sensor_data (datetime, sensor_id, co2, temperature, humidity, mode, sensor_type, cyclicName)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now_ms, sensor_id, co2, temp, humid, mode, sensor_type, cyclicName))
        conn.commit()
    except Exception as err:
        print(f"error when save in database {err}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────
# Main loop (drain queue แบบไม่พึ่ง .empty())
# ─────────────────────────────────────────────────────────────
def main():
    print("start.... main try to get queue")
    set_queue = Queue()
    poller = SensorPoller(ui_queue=set_queue, polling_interval=10)

    # เริ่มอ่าน 10 วินาที แล้วหยุด จากนั้นดูดคิวให้หมด
    poller.start()
    time.sleep(10)
    poller.stop()

    while True:
        try:
            data_sensor = set_queue.get_nowait()  # แทนการเช็ค empty()
        except Empty:
            break

        data = data_sensor['data']
        now_ms = int(time.time() * 1000)
        if data['sensor_id'] == 51:
            save_to_db(now_ms=now_ms,
                       sensor_id=data['sensor_id'],
                       co2=data['co2'],
                       temp=data['temperature'],
                       humid=data['humidity'],
                       mode="test",
                       sensor_type="type_k")
        else:
            save_to_db(now_ms=now_ms,
                       sensor_id=data['sensor_id'],
                       co2=data['co2'],
                       temp=data['temperature'],
                       humid=data['humidity'],
                       mode="test",
                       sensor_type="tongdy")

    # พักเล็กน้อยก่อนรอบถัดไป
    time.sleep(5)

# ─────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Started")
    service_stop, supervisor_thread = start_checking_thread()
    try:
        while True:
            main()
    except KeyboardInterrupt:
        pass
    finally:
        service_stop.set()
        supervisor_thread.join(timeout=3)
