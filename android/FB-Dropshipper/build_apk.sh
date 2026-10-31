#!/bin/bash
# Build APK using Android SDK / Gradle / Android Studio
# Requires: Android SDK, Gradle, Java 17+, build-tools
# Side-load output: app/build/outputs/apk/release/app-release-unsigned.apk

cd "$(dirname "$0")"
./gradlew assembleRelease 2>&1 | tee build.log

echo "APK built at: app/build/outputs/apk/release/app-release-unsigned.apk"
echo "Sign with jarsigner / apksigner for installation outside Play Store."
echo "Side-load via adb install -r app-release-unsigned.apk"
