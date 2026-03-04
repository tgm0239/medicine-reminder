package org.medreminder.app;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.app.NotificationManager;
import android.app.NotificationChannel;
import android.app.PendingIntent;
import android.media.RingtoneManager;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Build;
import android.os.PowerManager;
import android.util.Log;

import androidx.core.app.NotificationCompat;

import org.kivy.android.PythonActivity;

public class ReminderReceiver extends BroadcastReceiver {
    private static final String CHANNEL_ID = "medicine_channel";

    @Override
    public void onReceive(Context context, Intent intent) {
        String medicineName = intent.getStringExtra("medicine_name");
        String dosage = intent.getStringExtra("dosage");
        String notes = intent.getStringExtra("notes");
        String time = intent.getStringExtra("time");
        int requestCode = intent.getIntExtra("request_code", 0);

        Log.d("ReminderReceiver", "Alarm received: " + medicineName + " " + time);

        // 唤醒屏幕
        PowerManager pm = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
        PowerManager.WakeLock wl = pm.newWakeLock(
            PowerManager.FULL_WAKE_LOCK | PowerManager.ACQUIRE_CAUSES_WAKEUP | PowerManager.ON_AFTER_RELEASE,
            "MedicineReminder:WakeLock"
        );
        wl.acquire(5000); // 持有5秒

        // 播放默认闹钟铃声
        playAlarmSound(context);

        // 显示通知
        showNotification(context, medicineName, dosage, time, requestCode);
    }

    private void playAlarmSound(Context context) {
        try {
            Uri alarmSound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
            if (alarmSound == null) {
                alarmSound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
            }
            MediaPlayer player = MediaPlayer.create(context, alarmSound);
            player.setAudioStreamType(AudioManager.STREAM_ALARM);
            player.setLooping(false);
            player.start();
            player.setOnCompletionListener(mp -> {
                mp.release();
            });
        } catch (Exception e) {
            Log.e("ReminderReceiver", "Play sound failed", e);
        }
    }

    private void showNotification(Context context, String name, String dosage, String time, int requestCode) {
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);

        // 创建通知渠道（Android 8+）
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "服药提醒",
                NotificationManager.IMPORTANCE_HIGH
            );
            channel.setDescription("到点服药提醒");
            channel.enableVibration(true);
            channel.setVibrationPattern(new long[]{1000, 1000});
            manager.createNotificationChannel(channel);
        }

        // 点击通知后打开应用
        Intent intent = new Intent(context, PythonActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        PendingIntent pendingIntent = PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0)
        );

        // 构建通知
        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(context.getApplicationInfo().icon)
            .setContentTitle("⏰ 吃药提醒")
            .setContentText(name + " · " + dosage + " (" + time + ")")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setFullScreenIntent(pendingIntent, true)  // 锁屏显示
            .setAutoCancel(true)
            .setContentIntent(pendingIntent);

        manager.notify(requestCode, builder.build());
    }
}
