# -*- coding: utf-8 -*-
import sqlite3
import datetime
import json

class MedicineDatabase:
    def __init__(self):
        self.db_name = 'medicine.db'
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dosage TEXT,
                schedule TEXT,
                notes TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER,
                schedule_id INTEGER,
                scheduled_time TEXT,
                actual_time TEXT,
                status TEXT,
                dosage TEXT,
                notes TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_medicine(self, name, dosage, schedule, notes=""):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO medicines (name, dosage, schedule, notes)
            VALUES (?, ?, ?, ?)
        ''', (name, dosage, json.dumps(schedule), notes))
        med_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return med_id

    def get_today_schedule(self):
        today = datetime.date.today()
        weekday = today.weekday()
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM medicines WHERE is_active = 1')
        rows = cursor.fetchall()
        conn.close()
        schedule = []
        for row in rows:
            med_id, name, dosage, sched_json, notes = row[0], row[1], row[2], row[3], row[5]
            try:
                sched_list = json.loads(sched_json) if sched_json else []
            except:
                sched_list = []
            for s in sched_list:
                days = s.get('days', [0, 1, 2, 3, 4, 5, 6])
                if weekday in days or days == []:
                    schedule.append({
                        'id': s.get('id', 0),
                        'medicine_id': med_id,
                        'medicine_name': name,
                        'dosage': s.get('dosage', dosage),
                        'time': s.get('time', '08:00'),
                        'notes': s.get('notes', ''),
                        'medicine_notes': notes
                    })
        schedule.sort(key=lambda x: x['time'])
        return schedule

    def add_record(self, medicine_id, schedule_id, scheduled_time, status='taken', dosage="", notes=""):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO records (medicine_id, schedule_id, scheduled_time, actual_time, status, dosage, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (medicine_id, schedule_id, scheduled_time, now, status, dosage, notes))
        conn.commit()
        conn.close()

    def update_medicine_schedule(self, medicine_id, schedule):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('UPDATE medicines SET schedule = ? WHERE id = ?', (json.dumps(schedule), medicine_id))
        conn.commit()
        conn.close()

    def get_medicine_schedule(self, medicine_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT schedule FROM medicines WHERE id = ?', (medicine_id,))
        res = cursor.fetchone()
        conn.close()
        if res and res[0]:
            return json.loads(res[0])
        return []