[app]

# (str) Title of your application
title = CampusCompass Mobile

# (str) Package name
package.name = campuscompass

# (str) Package domain (needed for android/ios packaging)
package.domain = org.campuscompass

# (source.dir) Source code directory, must be ** relative ** to buildozer.spec
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,images/*

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, docs

# (list) List of exclusions using pattern matching
# source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 1.0.0

# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (string) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (list) Permissions
android.permissions = INTERNET,ACCESS_COARSE_LOCATION,ACCESS_FINE_LOCATION,ACCESS_NETWORK_STATE

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 31

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android app theme, default is ok for Kivy-based app
android.theme = "@android:style/Theme.NoTitleBar"

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a,armeabi-v7a

# (bool) Enable AndroidX support
android.enable_androidx = True

# (list) Pattern to whitelist for the whole project
android.whitelist = lib-dynload/termios.so

# (list) This is a list of java files for android. Each should start with only a slash
android.add_src =

# (list) Pattern to whitelist the use of the ** ws ** module
# android.whitelist = lib-dynload/termios.so

# (bool) Copy library instead of making a libpymodules.so
# android.copy_libs = 1

# (str) The Android logcat filters to use when running logcat before each build.
# android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
# android.copy_libs = 1

# (str) The Android logcat filters to use when running logcat before each build.
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
# android.copy_libs = 1

# (str) The Android logcat filters to use when running logcat before each build.
# android.logcat_filters = *:S python:D

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since extra jars can slow
# down the build process. Allows wildcards matching with glob syntax:
# OUYA-ODK/libs/*.jar

# (list) List of Java files for Android
# android.add_src =

# (list) Gradle dependencies
android.gradle_dependencies = com.google.android.material:material:1.6.1

# (bool) Gradle dependencies
android.add_gradle_repositories = true

# (list) Pattern to whitelist for the whole project
#android.whitelist = lib-dynload/termios.so

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The Android logcat filters to use when running logcat before each build.
#android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) The Android logcat filters to use when running logcat before each build.
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The Android logcat filters to use when running logcat before each build.
#android.logcat_filters = *:S python:D

# (list) List of class for Android intent
# android.add_src =

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning upon buildozer run if buildozer.spec is older than buildozer.py
warn_on_root = 1
