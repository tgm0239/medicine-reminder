[app]

# 应用名称（显示在手机桌面的名字）
title = 吃药提醒

# 包名（唯一标识，不要和别人重复）
package.name = medicinereminder
package.domain = org.yourname

# 源码目录（. 表示当前目录）
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,java,xml

# 版本号（静态版本，只保留这一行）
version = 1.0.0

# ===== 依赖库（不要删减）=====
requirements = python3,kivy,sqlite3,plyer,pyjnius,pygame,android

# 屏幕方向
orientation = portrait
fullscreen = 0

# ===== Android 权限 =====
android.permissions = INTERNET, VIBRATE, WAKE_LOCK, RECEIVE_BOOT_COMPLETED

# ===== SDK/NDK 版本 =====
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# ===== 包含你的 Java 广播接收器 =====
android.add_src = .

# ===== 使用自定义 AndroidManifest =====
android.manifest = AndroidManifest.tmpl.xml

# ===== 应用图标（请准备 icon.png 放在项目根目录）=====
icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
android.build_tools = 33.0.2
