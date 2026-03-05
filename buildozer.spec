name: Build APK

on: [push, workflow_dispatch]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.8'
      - name: Install system dependencies
        run: |
          sudo apt update
          sudo apt install -y git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses-dev cmake libffi-dev libssl-dev wget
      - name: Install buildozer
        run: |
          pip install --user --upgrade buildozer cython
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      # 创建 buildozer 期望的 SDK 目录
      - name: Create SDK directory
        run: |
          mkdir -p /home/runner/.buildozer/android/platform/android-sdk
          cd /home/runner/.buildozer/android/platform/android-sdk
      # 手动下载并安装 commandlinetools
      - name: Install Android SDK manually
        run: |
          export ANDROID_HOME=/home/runner/.buildozer/android/platform/android-sdk
          mkdir -p $ANDROID_HOME/cmdline-tools
          cd $ANDROID_HOME/cmdline-tools
          wget -q https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip
          unzip -q commandlinetools-linux-9477386_latest.zip
          mv cmdline-tools latest
          # 将 sdkmanager 加入 PATH
          echo "$ANDROID_HOME/cmdline-tools/latest/bin" >> $GITHUB_PATH
          export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
          # 接受所有许可证
          yes | sdkmanager --licenses
          # 安装必要的 SDK 组件（稳定版本）
          sdkmanager "platform-tools" "platforms;android-33" "build-tools;33.0.2"
          # 为了兼容旧的 buildozer 路径，创建 tools/bin 软链接
          mkdir -p $ANDROID_HOME/tools/bin
          ln -s $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager $ANDROID_HOME/tools/bin/sdkmanager
      # 设置 Android 环境变量
      - name: Set Android environment variables
        run: |
          echo "ANDROID_HOME=/home/runner/.buildozer/android/platform/android-sdk" >> $GITHUB_ENV
          echo "ANDROID_SDK_ROOT=/home/runner/.buildozer/android/platform/android-sdk" >> $GITHUB_ENV
      # 安装 autoconf-archive 并强制使用 buildozer 的 NDK
      - name: Install autotools and fix NDK path
        run: |
          sudo apt update
          sudo apt install -y autoconf-archive libtool-bin
          # 设置 NDK 路径为 buildozer 下载的版本（r25b）
          echo "ANDROID_NDK=/home/runner/.buildozer/android/platform/android-ndk-r25b" >> $GITHUB_ENV
          echo "ANDROID_NDK_HOME=/home/runner/.buildozer/android/platform/android-ndk-r25b" >> $GITHUB_ENV
      # ===== 关键修复：完全覆盖 buildozer.spec，避免重复配置 =====
      - name: Write correct buildozer.spec
        run: |
          cat > buildozer.spec << 'EOF'
[app]

# 应用名称
title = 吃药提醒

# 包名
package.name = medicinereminder
package.domain = org.yourname

# 源码目录
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,java,xml

# 版本号
version = 1.0.0

# 依赖库
requirements = python3,kivy,sqlite3,plyer,pyjnius,pygame,android

# 屏幕方向
orientation = portrait
fullscreen = 0

# Android 权限
android.permissions = INTERNET, VIBRATE, WAKE_LOCK, RECEIVE_BOOT_COMPLETED

# SDK/NDK 版本
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.build_tools = 33.0.2
android.ndk_path = /home/runner/.buildozer/android/platform/android-ndk-r25b

# 包含 Java 源码
android.add_src = .

# 使用自定义 AndroidManifest
android.manifest = AndroidManifest.tmpl.xml

# 图标（如果有）
icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
EOF
      - name: Build APK
        run: |
          cd $GITHUB_WORKSPACE
          buildozer -v android debug
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: app-debug
          path: bin/*.apk

