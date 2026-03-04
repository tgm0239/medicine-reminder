[app]

title = 吃药提醒
package.name = medicinereminder
package.domain = org.medreminder.app

source.dir = .
source.include_exts = py,png,jpg,kv,ttf,mp3,wav,java,xml

version = 0.1
version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/main.py

requirements = python3,kivy,sqlite3,plyer,pyjnius,pygame,android

orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.0.0
fullscreen = 0

# Android 权限
android.permissions = INTERNET, VIBRATE, RECEIVE_BOOT_COMPLETED, WAKE_LOCK, FOREGROUND_SERVICE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# 包含自定义 Java 源码
android.add_src = .

# 使用自定义 AndroidManifest 模板
android.manifest = AndroidManifest.tmpl.xml

# 图标（请准备 icon.png 放在项目根目录）
icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1