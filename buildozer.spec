[app]
title = 吃药提醒
package.name = medicinereminder
package.domain = org.yourname
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,java,xml
version = 1.0.0
requirements = python3,kivy,sqlite3,plyer,pyjnius,android
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, VIBRATE, WAKE_LOCK, RECEIVE_BOOT_COMPLETED
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.build_tools = 33.0.2
android.archs = arm64-v8a
android.add_src = .
android.manifest = AndroidManifest.tmpl.xml
# icon.filename = %(source.dir)s/icon.png  # 如果没有图标就注释掉
[buildozer]
log_level = 2
warn_on_root = 1
