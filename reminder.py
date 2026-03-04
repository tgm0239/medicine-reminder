# -*- coding: utf-8 -*-
from kivy.utils import platform
from jnius import autoclass
from android import mActivity
import json

if platform == 'android':
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    Intent = autoclass('android.content.Intent')
    PendingIntent = autoclass('android.app.PendingIntent')
    AlarmManager = autoclass('android.app.AlarmManager')
    Calendar = autoclass('java.util.Calendar')

    # 导入自定义广播接收器（包名需与 Java 文件一致）
    ReminderReceiver = autoclass('org.medreminder.app.ReminderReceiver')

def set_alarm(time_str, medicine_name, dosage, notes, request_code):
    """设置单个闹钟"""
    if platform != 'android':
        print('Alarm only supported on Android')
        return

    try:
        cal = Calendar.getInstance()
        now = Calendar.getInstance()
        hour, minute = map(int, time_str.split(':'))
        cal.set(Calendar.HOUR_OF_DAY, hour)
        cal.set(Calendar.MINUTE, minute)
        cal.set(Calendar.SECOND, 0)
        cal.set(Calendar.MILLISECOND, 0)

        # 如果时间已过，设置为明天
        if cal.getTimeInMillis() < now.getTimeInMillis():
            cal.add(Calendar.DAY_OF_MONTH, 1)

        intent = Intent(PythonActivity.mActivity, ReminderReceiver)
        intent.putExtra('medicine_name', medicine_name)
        intent.putExtra('dosage', dosage)
        intent.putExtra('notes', notes)
        intent.putExtra('time', time_str)
        intent.putExtra('request_code', request_code)

        # FLAG_IMMUTABLE 适配 Android 12+
        flags = PendingIntent.FLAG_UPDATE_CURRENT
        if hasattr(PendingIntent, 'FLAG_IMMUTABLE'):
            flags |= PendingIntent.FLAG_IMMUTABLE

        pending = PendingIntent.getBroadcast(
            PythonActivity.mActivity,
            request_code,
            intent,
            flags
        )

        alarm = PythonActivity.mActivity.getSystemService(Context.ALARM_SERVICE)
        alarm.setExact(AlarmManager.RTC_WAKEUP, cal.getTimeInMillis(), pending)
        print(f'Alarm set for {time_str} (req: {request_code})')

    except Exception as e:
        print(f'Failed to set alarm: {e}')

def cancel_alarm(request_code):
    """取消闹钟"""
    if platform != 'android':
        return
    try:
        intent = Intent(PythonActivity.mActivity, ReminderReceiver)
        flags = PendingIntent.FLAG_UPDATE_CURRENT
        if hasattr(PendingIntent, 'FLAG_IMMUTABLE'):
            flags |= PendingIntent.FLAG_IMMUTABLE
        pending = PendingIntent.getBroadcast(
            PythonActivity.mActivity,
            request_code,
            intent,
            flags
        )
        alarm = PythonActivity.mActivity.getSystemService(Context.ALARM_SERVICE)
        alarm.cancel(pending)
        pending.cancel()
        print(f'Alarm cancelled (req: {request_code})')
    except Exception as e:
        print(f'Failed to cancel alarm: {e}')