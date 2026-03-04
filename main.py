# -*- coding: utf-8 -*-

# ========== 【1】优先设置 Kivy 全局字体配置 ==========
import os
import sys
from kivy.config import Config

if sys.platform == 'win32':
    font_candidates = [
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/simhei.ttf',
    ]
    for path in font_candidates:
        if os.path.exists(path):
            Config.set('kivy', 'default_font', ['WinFont', path])
            print(f'✅ Windows 强制设置默认字体: {path}')
            break
    else:
        print('⚠️ Windows 未找到中文字体')

# ========== 【2】手机模式配置 ==========
from kivy.core.window import Window
Window.size = (400, 700)
Window.clearcolor = (1, 1, 1, 1)
Window.resizable = False

# ========== 【3】导入 Kivy 核心模块 ==========
from kivy.core.text import LabelBase
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.utils import platform
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

if sys.platform == 'win32' and 'path' in locals() and os.path.exists(path):
    LabelBase.register(name='WinFont', fn_regular=path)
elif platform == 'android':
    Config.set('kivy', 'default_font', ['Roboto', 'DroidSansFallback'])
    print('✅ Android 使用系统内置字体')

# ========== 【4】导入自定义模块 ==========
from database import MedicineDatabase

if platform == 'android':
    from reminder import set_alarm, cancel_alarm
    from plyer import tts
else:
    def set_alarm(*args, **kwargs): print(f'[模拟] 设置闹钟: {args}')
    def cancel_alarm(*args, **kwargs): print(f'[模拟] 取消闹钟: {args}')
    class MockTTS:
        @staticmethod
        def speak(text): print(f'[TTS] {text}')
    tts = MockTTS()

# ========== 【5】导出历史记录工具函数 ==========
def export_records_to_csv(records, filename):
    import csv
    import os
    from datetime import datetime

    if platform == 'android':
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
        from android.storage import primary_external_storage_path
        download_path = os.path.join(primary_external_storage_path(), 'Download')
        if not os.path.exists(download_path):
            download_path = os.path.expanduser('~')
    else:
        download_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        if not os.path.exists(download_path):
            download_path = os.getcwd()

    filepath = os.path.join(download_path, filename)

    try:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['药品名称', '剂量', '预定时间', '实际记录时间', '状态', '备注'])
            for r in records:
                status_map = {'taken': '已服用', 'skipped': '跳过', 'missed': '漏服'}
                status = status_map.get(r[2], r[2])
                writer.writerow([r[3], r[4], r[0], r[1], status, r[5] if len(r) > 5 else ''])
        return filepath
    except Exception as e:
        print(f'导出失败: {e}')
        return None

# ========== 【6】主界面卡片（生机活泼版）==========
class ScheduleCard(BoxLayout):
    """今日安排卡片——字体放大、颜色鲜活、间距紧凑"""
    def __init__(self, medicine_name='', time='', dosage='', notes='',
                 medicine_id=0, schedule_id=0, **kwargs):
        medicine_name = str(medicine_name or '')
        time = str(time or '')
        dosage = str(dosage or '默认剂量')
        notes = str(notes or '')

        self.medicine_id = medicine_id
        self.schedule_id = schedule_id
        self.medicine_name = medicine_name
        self.time = time
        self.dosage = dosage
        self.notes = notes

        kwargs.pop('medicine_id', None)
        kwargs.pop('schedule_id', None)
        kwargs.pop('medicine_name', None)
        kwargs.pop('time', None)
        kwargs.pop('dosage', None)
        kwargs.pop('notes', None)

        super().__init__(**kwargs)

        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(110)
        self.padding = [dp(10), dp(6), dp(10), dp(6)]
        self.spacing = dp(4)

        # 第1行：时间（亮蓝），编辑（鲜亮蓝），已服用（鲜绿）
        row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), spacing=dp(6))
        time_label = Label(
            text=f'🕒 {self.time}',
            font_size=dp(18),
            bold=True,
            color=(0.1, 0.5, 0.9, 1),
            halign='left',
            valign='middle',
            size_hint_x=0.5
        )
        time_label.bind(size=time_label.setter('text_size'))
        row1.add_widget(time_label)

        edit_btn = Button(
            text='编辑',
            size_hint=(0.25, 1),
            background_color=(0.3, 0.6, 1.0, 1),
            color=(1, 1, 1, 1),
            font_size=dp(15)
        )
        edit_btn.bind(on_release=self.edit_schedule)
        row1.add_widget(edit_btn)

        taken_btn = Button(
            text='✓ 已服用',
            size_hint=(0.25, 1),
            background_color=(0.2, 0.8, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=dp(15)
        )
        taken_btn.bind(on_release=self.taken)
        row1.add_widget(taken_btn)
        self.add_widget(row1)

        # 第2行：药名（左黑粗），剂量（中灰），备注（右黑粗，直接显示内容）
        row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32), spacing=dp(6))
        name_label = Label(
            text=self.medicine_name,
            font_size=dp(17),
            bold=True,
            color=(0, 0, 0, 1),
            halign='left',
            valign='middle',
            size_hint_x=0.35
        )
        name_label.bind(size=name_label.setter('text_size'))
        row2.add_widget(name_label)

        dosage_label = Label(
            text=self.dosage,
            font_size=dp(16),
            bold=False,
            color=(0.3, 0.3, 0.3, 1),
            halign='center',
            valign='middle',
            size_hint_x=0.3
        )
        dosage_label.bind(size=dosage_label.setter('text_size'))
        row2.add_widget(dosage_label)

        notes_label = Label(
            text=self.notes if self.notes else '',
            font_size=dp(16),
            bold=True,
            color=(0, 0, 0, 1),
            halign='right',
            valign='middle',
            size_hint_x=0.35
        )
        notes_label.bind(size=notes_label.setter('text_size'))
        row2.add_widget(notes_label)
        self.add_widget(row2)

    def taken(self, btn):
        app = App.get_running_app()
        app.record_taken(self.medicine_id, self.schedule_id, self.time, self.dosage, self.notes)
        self.parent.remove_widget(self)

    def edit_schedule(self, btn):
        app = App.get_running_app()
        app.open_schedule_editor(self.medicine_id)


class TodayScheduleScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(12)
        self.spacing = dp(10)

        title = Label(
            text='今日服药安排',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(20),
            color=(0.1, 0.5, 0.9, 1),
            bold=True
        )
        self.add_widget(title)

        self.scroll = ScrollView()
        self.list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        self.add_widget(self.scroll)

        # 底部按钮栏（仅保留添加药品和历史）
        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(12))
        add_btn = Button(
            text='+ 添加药品',
            background_color=(0.2, 0.6, 1.0, 1),
            color=(1, 1, 1, 1),
            font_size=dp(16)
        )
        add_btn.bind(on_release=lambda x: App.get_running_app().open_add_medicine())
        history_btn = Button(
            text='📋 历史',
            background_color=(1.0, 0.6, 0.1, 1),
            color=(1, 1, 1, 1),
            font_size=dp(16)
        )
        history_btn.bind(on_release=lambda x: App.get_running_app().open_history())
        btn_layout.add_widget(add_btn)
        btn_layout.add_widget(history_btn)
        self.add_widget(btn_layout)

    def load_schedule(self):
        self.list_layout.clear_widgets()
        app = App.get_running_app()
        schedule = app.db.get_today_schedule()
        if not schedule:
            lbl = Label(
                text='今天没有需要服用的药品',
                size_hint_y=None,
                height=dp(50),
                color=(0.6, 0.6, 0.6, 1)
            )
            self.list_layout.add_widget(lbl)
            return

        stats = f"今日共有 {len(schedule)} 次服药"
        lbl = Label(
            text=stats,
            size_hint_y=None,
            height=dp(30),
            font_size=dp(14),
            color=(0.3, 0.3, 0.3, 1)
        )
        self.list_layout.add_widget(lbl)

        for item in schedule:
            medicine_name = str(item['medicine_name'] or '')
            time = str(item['time'] or '')
            dosage = str(item['dosage'] or '默认剂量')
            notes = str(item.get('notes') or item.get('medicine_notes') or '')
            medicine_id = int(item['medicine_id'])
            schedule_id = int(item['id'])

            card = ScheduleCard(
                medicine_name=medicine_name,
                time=time,
                dosage=dosage,
                notes=notes,
                medicine_id=medicine_id,
                schedule_id=schedule_id
            )
            self.list_layout.add_widget(card)


# ========== 【7】时间点编辑器——文字水平居中，通过padding模拟垂直居中 ==========
class TimePointRow(BoxLayout):
    """时间点编辑器单行——鲜亮按钮，文字水平居中，垂直方向通过padding调整"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.spacing = dp(8)
        self.padding = [dp(0), dp(2), dp(0), dp(2)]

        # 时间输入框：水平居中，垂直通过padding微调
        self.time_input = TextInput(
            text='08:00',
            size_hint_x=0.2,
            multiline=False,
            hint_text='时间',
            halign='center',          # 水平居中
            background_color=(0.98, 0.98, 0.98, 1),
            foreground_color=(0, 0, 0, 1),
            font_size=dp(16),
            padding=[dp(6), dp(12)]   # 加大上下内边距，模拟垂直居中
        )
        self.add_widget(self.time_input)

        # 剂量输入框：水平居中，垂直通过padding微调
        self.dosage_input = TextInput(
            text='',
            size_hint_x=0.2,
            multiline=False,
            hint_text='剂量',
            halign='center',          # 水平居中
            background_color=(0.98, 0.98, 0.98, 1),
            foreground_color=(0, 0, 0, 1),
            font_size=dp(16),
            padding=[dp(6), dp(12)]   # 加大上下内边距，模拟垂直居中
        )
        self.add_widget(self.dosage_input)

        # 每天/工作日/周末 按钮（鲜亮蓝色）
        self.day_btn = Button(
            text='每天',
            size_hint_x=0.2,
            background_color=(0.2, 0.6, 1.0, 1),
            color=(1, 1, 1, 1),
            font_size=dp(16),
            bold=True
        )
        self.day_btn.bind(on_release=self.toggle_days)
        self.add_widget(self.day_btn)
        self.selected_days = [0, 1, 2, 3, 4, 5, 6]

        # 说明输入框：水平居中，垂直通过padding微调
        self.notes_input = TextInput(
            text='',
            size_hint_x=0.25,
            multiline=False,
            hint_text='说明',
            halign='center',          # 水平居中
            background_color=(0.98, 0.98, 0.98, 1),
            foreground_color=(0, 0, 0, 1),
            font_size=dp(16),
            padding=[dp(6), dp(12)]   # 加大上下内边距，模拟垂直居中
        )
        self.add_widget(self.notes_input)

        # 删除按钮（鲜红色，文字「删除」）
        del_btn = Button(
            text='删除',
            size_hint_x=0.15,
            background_color=(1.0, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=dp(16),
            bold=True
        )
        del_btn.bind(on_release=lambda x: self.parent.remove_widget(self))
        self.add_widget(del_btn)

    def toggle_days(self, btn):
        if btn.text == '每天':
            btn.text = '工作日'
            self.selected_days = [0, 1, 2, 3, 4]
        elif btn.text == '工作日':
            btn.text = '周末'
            self.selected_days = [5, 6]
        else:
            btn.text = '每天'
            self.selected_days = [0, 1, 2, 3, 4, 5, 6]

    def get_data(self):
        return {
            'time': self.time_input.text.strip(),
            'dosage': self.dosage_input.text.strip(),
            'days': self.selected_days,
            'notes': self.notes_input.text.strip()
        }


class ScheduleEditorPopup(Popup):
    """时间安排编辑器弹窗——纯白明亮底板"""
    def __init__(self, medicine_name='', medicine_id=None, current_schedule=None, **kwargs):
        super().__init__(**kwargs)
        self.title = f'⏰ 时间安排 - {medicine_name}'
        self.size_hint = (0.95, 0.9)
        self.medicine_id = medicine_id
        self.schedule = None

        # 纯白明亮背景
        self.background = ''
        self.background_color = (1, 1, 1, 1)
        self.separator_color = (0.2, 0.6, 1.0, 1)
        self.separator_height = dp(2)

        main_layout = BoxLayout(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(12)
        )
        # 白色背景填充
        with main_layout.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        main_layout.bind(pos=self._update_rect, size=self._update_rect)

        info = Label(
            text='每个时间点可独立设置剂量、星期和说明',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(15),
            color=(0.2, 0.2, 0.2, 1),
            bold=False
        )
        main_layout.add_widget(info)

        scroll = ScrollView()
        self.rows_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(8))
        self.rows_layout.bind(minimum_height=self.rows_layout.setter('height'))
        scroll.add_widget(self.rows_layout)
        main_layout.add_widget(scroll)

        add_row_btn = Button(
            text='+ 添加时间点',
            size_hint_y=None,
            height=dp(44),
            background_color=(0.2, 0.6, 1.0, 1),
            color=(1, 1, 1, 1),
            font_size=dp(16)
        )
        add_row_btn.bind(on_release=self.add_time_row)
        main_layout.add_widget(add_row_btn)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(12))
        save_btn = Button(
            text='✓ 保存',
            background_color=(0.2, 0.8, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=dp(17)
        )
        save_btn.bind(on_release=self.save_schedule)
        cancel_btn = Button(
            text='✗ 取消',
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=dp(17)
        )
        cancel_btn.bind(on_release=self.dismiss)
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        main_layout.add_widget(btn_layout)

        self.content = main_layout

        if current_schedule:
            for s in current_schedule:
                self.add_time_row(None, s)

    def _update_rect(self, *args):
        self.rect.pos = self.content.pos
        self.rect.size = self.content.size

    def add_time_row(self, btn, sched_data=None):
        row = TimePointRow()
        if sched_data:
            row.time_input.text = sched_data.get('time', '08:00')
            row.dosage_input.text = sched_data.get('dosage', '')
            row.notes_input.text = sched_data.get('notes', '')
            days = sched_data.get('days', [0, 1, 2, 3, 4, 5, 6])
            row.selected_days = days
            if days == [0, 1, 2, 3, 4, 5, 6]:
                row.day_btn.text = '每天'
            elif days == [0, 1, 2, 3, 4]:
                row.day_btn.text = '工作日'
            elif days == [5, 6]:
                row.day_btn.text = '周末'
            else:
                row.day_btn.text = '自定义'
        self.rows_layout.add_widget(row)

    def save_schedule(self, btn):
        import datetime
        schedule = []
        for row in self.rows_layout.children:
            if isinstance(row, TimePointRow):
                data = row.get_data()
                if not data['time']:
                    self.show_error('时间不能为空')
                    return
                try:
                    datetime.datetime.strptime(data['time'], '%H:%M')
                except ValueError:
                    self.show_error('时间格式错误，请使用 HH:MM 格式')
                    return
                schedule.append(data)
        if not schedule:
            self.show_error('请至少添加一个时间点')
            return
        self.schedule = schedule
        app = App.get_running_app()
        if self.medicine_id:
            app.db.update_medicine_schedule(self.medicine_id, schedule)
            app.schedule_alarms_for_medicine(self.medicine_id, schedule)
        self.dismiss()
        app.refresh_today()

    def show_error(self, msg):
        popup = Popup(
            title='错误',
            content=Label(text=msg, color=(1, 0, 0, 1), font_size=dp(16)),
            size_hint=(0.6, 0.4)
        )
        popup.open()


# ========== 【8】主应用类（核心逻辑完全保留）==========
class MedicineReminderApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = MedicineDatabase()
        self.today_screen = None

        # 自动提醒跟踪
        self.reminder_tracker = {}
        self.taken_today = set()
        self.last_check_date = None

    def build(self):
        from kivy.core.text import Label as CoreLabel
        test_label = CoreLabel(text='测试字体')
        print(f'🔍 当前默认字体: {test_label.options.get("font_name")}')

        self.today_screen = TodayScheduleScreen()
        Clock.schedule_once(lambda dt: self.today_screen.load_schedule(), 0)
        Clock.schedule_interval(self.check_reminders, 60)
        return self.today_screen

    def on_start(self):
        self.schedule_all_alarms()
        if platform == 'android':
            self.show_toast('后台提醒已设置')

    # ---------- 提醒核心逻辑（三次重试+漏服）----------
    def check_reminders(self, dt):
        import datetime
        now = datetime.datetime.now()
        today_str = now.strftime('%Y-%m-%d')
        schedule = self.db.get_today_schedule()

        if self.last_check_date != today_str:
            self.reminder_tracker.clear()
            self.taken_today.clear()
            self.last_check_date = today_str

        for item in schedule:
            key = (item['medicine_id'], item['id'], today_str, item['time'])
            if key in self.taken_today:
                continue

            try:
                sched_time = datetime.datetime.strptime(f"{today_str} {item['time']}", '%Y-%m-%d %H:%M')
            except:
                continue

            if now < sched_time:
                continue

            delta_minutes = int((now - sched_time).total_seconds() / 60)

            if key not in self.reminder_tracker:
                self.reminder_tracker[key] = {
                    'reminder_count': 0,
                    'last_remind_time': None,
                    'status': 'pending'
                }
            state = self.reminder_tracker[key]
            if state['status'] in ('taken', 'missed'):
                continue

            triggered = False
            if state['reminder_count'] == 0 and delta_minutes == 0:
                self.trigger_reminder(item)
                state['reminder_count'] = 1
                state['last_remind_time'] = now
                triggered = True
            elif state['reminder_count'] == 1 and delta_minutes >= 10:
                self.trigger_reminder(item)
                state['reminder_count'] = 2
                state['last_remind_time'] = now
                triggered = True
            elif state['reminder_count'] == 2 and delta_minutes >= 20:
                self.trigger_reminder(item)
                state['reminder_count'] = 3
                state['last_remind_time'] = now
                triggered = True
            elif state['reminder_count'] == 3 and delta_minutes >= 30:
                self.auto_missed(item, key)
                state['status'] = 'missed'
                self.taken_today.add(key)
                triggered = False

    def trigger_reminder(self, item):
        self.show_reminder_popup(item)
        if platform == 'android':
            tts.speak('请按时服药')
        else:
            print('🔊 语音提醒：请按时服药')

    def auto_missed(self, item, key):
        self.db.add_record(
            item['medicine_id'],
            item['id'],
            item['time'],
            status='missed',
            dosage=item['dosage'],
            notes='系统自动标记：漏服'
        )
        print(f'⏭️ 漏服记录: {item["medicine_name"]} {item["time"]}')
        self.show_toast('漏服已记录')

    # ---------- 记录服药 ----------
    def record_taken(self, medicine_id, schedule_id, scheduled_time, dosage, notes):
        self.db.add_record(medicine_id, schedule_id, scheduled_time, 'taken', dosage, notes)

        today = datetime.date.today().strftime('%Y-%m-%d')
        key = (medicine_id, schedule_id, today, scheduled_time)
        self.taken_today.add(key)
        if key in self.reminder_tracker:
            self.reminder_tracker[key]['status'] = 'taken'

        if platform == 'android':
            req_code = hash(f"{medicine_id}_{schedule_id}_{scheduled_time}") % 1000000
            cancel_alarm(req_code)

        self.show_toast('已记录服用')
        self.refresh_today()

    # ---------- 后台闹钟（Android AlarmManager）----------
    def schedule_alarms_for_medicine(self, medicine_id, schedule):
        if platform != 'android':
            return
        import sqlite3
        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT name, dosage FROM medicines WHERE id=?', (medicine_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return
        name, default_dosage = row
        for s in schedule:
            req_code = hash(f"{medicine_id}_{s['id']}_{s['time']}") % 1000000
            dosage = s['dosage'] or default_dosage
            notes = s.get('notes', '')
            set_alarm(s['time'], name, dosage, notes, req_code)

    def schedule_all_alarms(self):
        if platform != 'android':
            return
        import sqlite3
        import json
        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, dosage, schedule FROM medicines WHERE is_active=1')
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            med_id, name, dosage, sched_json = row
            try:
                sched = json.loads(sched_json) if sched_json else []
            except:
                sched = []
            for s in sched:
                req_code = hash(f"{med_id}_{s['id']}_{s['time']}") % 1000000
                s_dosage = s.get('dosage', dosage)
                notes = s.get('notes', '')
                set_alarm(s['time'], name, s_dosage, notes, req_code)

    # ---------- 药品管理 ----------
    def open_add_medicine(self):
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text='药品名称', size_hint_y=None, height=dp(30), color=(0,0,0,1), font_size=dp(16)))
        name_input = TextInput(multiline=False, background_color=(0.98,0.98,0.98,1), font_size=dp(16))
        content.add_widget(name_input)
        content.add_widget(Label(text='默认剂量', size_hint_y=None, height=dp(30), color=(0,0,0,1), font_size=dp(16)))
        dosage_input = TextInput(text='1片', multiline=False, background_color=(0.98,0.98,0.98,1), font_size=dp(16))
        content.add_widget(dosage_input)
        content.add_widget(Label(text='备注(可选)', size_hint_y=None, height=dp(30), color=(0,0,0,1), font_size=dp(16)))
        notes_input = TextInput(multiline=False, background_color=(0.98,0.98,0.98,1), font_size=dp(16))
        content.add_widget(notes_input)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        save_btn = Button(text='下一步', background_color=(0.2,0.8,0.2,1), color=(1,1,1,1), font_size=dp(16))
        cancel_btn = Button(text='取消', background_color=(0.9,0.3,0.3,1), color=(1,1,1,1), font_size=dp(16))
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(title='添加药品', content=content, size_hint=(0.8, 0.6))
        save_btn.bind(on_release=lambda x: self.do_add_medicine(
            name_input.text.strip(),
            dosage_input.text.strip(),
            notes_input.text.strip(),
            popup
        ))
        cancel_btn.bind(on_release=popup.dismiss)
        popup.open()

    def do_add_medicine(self, name, dosage, notes, popup):
        popup.dismiss()
        if not name:
            self.show_error('药品名称不能为空')
            return
        if not dosage:
            dosage = '1片'
        editor = ScheduleEditorPopup(medicine_name=name)
        editor.bind(on_dismiss=lambda x: self._add_medicine_callback(name, dosage, notes, editor.schedule))
        editor.open()

    def _add_medicine_callback(self, name, dosage, notes, schedule):
        if schedule:
            med_id = self.db.add_medicine(name, dosage, schedule, notes)
            self.schedule_alarms_for_medicine(med_id, schedule)
            self.refresh_today()

    def open_schedule_editor(self, medicine_id):
        sched = self.db.get_medicine_schedule(medicine_id)
        import sqlite3
        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM medicines WHERE id=?', (medicine_id,))
        row = cursor.fetchone()
        conn.close()
        name = row[0] if row else '未知'
        editor = ScheduleEditorPopup(
            medicine_name=name,
            medicine_id=medicine_id,
            current_schedule=sched
        )
        editor.bind(on_dismiss=lambda x: self.refresh_today())
        editor.open()

    # ---------- 历史记录 + 导出CSV ----------
    def open_history(self):
        import sqlite3
        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.scheduled_time, r.actual_time, r.status, m.name, r.dosage, r.notes
            FROM records r
            JOIN medicines m ON r.medicine_id = m.id
            ORDER BY r.actual_time DESC
            LIMIT 200
        ''')
        rows = cursor.fetchall()
        conn.close()

        content = BoxLayout(orientation='vertical')
        scroll = ScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        grid.bind(minimum_height=grid.setter('height'))

        if not rows:
            grid.add_widget(Label(text='暂无历史记录', size_hint_y=None, height=dp(50), color=(0.5,0.5,0.5,1), font_size=dp(16)))
        else:
            for r in rows:
                status_map = {'taken': '✓ 已服', 'skipped': '○ 跳过', 'missed': '✗ 漏服'}
                status = status_map.get(r[2], r[2])
                text = f"{r[3]} - {r[4]}\n{str(r[0])}  {status}"
                if r[5]:
                    text += f"\n备注: {r[5]}"
                grid.add_widget(Label(text=text, size_hint_y=None, height=dp(60), color=(0,0,0,1), font_size=dp(14)))

        scroll.add_widget(grid)
        content.add_widget(scroll)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(12))
        close_btn = Button(text='关闭', background_color=(0.5,0.5,0.5,1), color=(1,1,1,1), font_size=dp(16))
        export_btn = Button(text='📤 导出CSV', background_color=(0.2,0.6,1.0,1), color=(1,1,1,1), font_size=dp(16))
        btn_layout.add_widget(export_btn)
        btn_layout.add_widget(close_btn)
        content.add_widget(btn_layout)

        popup = Popup(title='服药历史', content=content, size_hint=(0.9, 0.9))

        def do_export(instance):
            if not rows:
                self.show_toast('无记录可导出')
                return
            from datetime import datetime
            filename = f'服药记录_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            filepath = export_records_to_csv(rows, filename)
            if filepath:
                self.show_toast(f'已导出至: {filepath}')
            else:
                self.show_error('导出失败')

        export_btn.bind(on_release=do_export)
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    # ---------- 工具函数 ----------
    def show_toast(self, msg):
        if platform == 'android':
            from android.runnable import run_on_ui_thread
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Toast = autoclass('android.widget.Toast')
            @run_on_ui_thread
            def show():
                Toast.makeText(PythonActivity.mActivity, msg, Toast.LENGTH_SHORT).show()
            show()
        else:
            popup = Popup(
                title='提示',
                content=Label(text=msg, color=(0,0,0,1), font_size=dp(16)),
                size_hint=(0.5, 0.3)
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)

    def show_error(self, msg):
        popup = Popup(
            title='错误',
            content=Label(text=msg, color=(1, 0, 0, 1), font_size=dp(16)),
            size_hint=(0.6, 0.4)
        )
        popup.open()

    def refresh_today(self):
        if self.today_screen:
            self.today_screen.load_schedule()

    def show_reminder_popup(self, item):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        content.add_widget(Label(
            text='💊 该吃药啦！',
            font_size=dp(24),
            color=(0.9, 0.1, 0.1, 1),
            bold=True
        ))
        content.add_widget(Label(
            text=str(item['medicine_name'] or ''),
            font_size=dp(20),
            color=(0, 0, 0, 1)
        ))
        content.add_widget(Label(
            text=f"时间: {str(item['time'] or '')}",
            font_size=dp(18),
            color=(0.2, 0.2, 0.2, 1)
        ))
        content.add_widget(Label(
            text=f"剂量: {str(item['dosage'] or '')}",
            font_size=dp(18),
            color=(0.2, 0.2, 0.2, 1)
        ))
        btn = Button(
            text='✓ 已服用',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.2, 0.8, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=dp(18)
        )
        popup = Popup(
            title='提醒',
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=False
        )
        btn.bind(on_release=lambda x: [
            self.record_taken(
                item['medicine_id'],
                item['id'],
                item['time'],
                item['dosage'],
                item.get('notes', '')
            ),
            popup.dismiss()
        ])
        content.add_widget(btn)
        popup.open()


if __name__ == '__main__':
    import datetime
    MedicineReminderApp().run()