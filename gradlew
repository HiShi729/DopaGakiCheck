#!/bin/sh
# Bootstrap the official Gradle 8.13 wrapper JAR and verify its published SHA-256.
# The JAR is not bundled because this environment cannot download binary SDK tools.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
JAR="$ROOT/gradle/wrapper/gradle-wrapper.jar"
SUM='81a82aaea5abcc8ff68b3dfcb58b3c3c429378efd98e7433460610fecd7ae45f'
if [ ! -f "$JAR" ]; then
    echo 'Downloading verified Gradle 8.13 wrapper JAR (first run only)...'
    command -v curl >/dev/null 2>&1 || { echo 'curl is required' >&2; exit 1; }
    TMP="$JAR.download.$$"
    trap 'rm -f "$TMP"' EXIT HUP INT TERM
    curl -fLsS --retry 3 'https://services.gradle.org/distributions/gradle-8.13-wrapper.jar' -o "$TMP"
    ACTUAL=$(shasum -a 256 "$TMP" | cut -d ' ' -f 1)
    if [ "$ACTUAL" != "$SUM" ]; then
        echo 'Gradle wrapper checksum mismatch; refusing to execute it' >&2
        exit 1
    fi
    mv "$TMP" "$JAR"
    trap - EXIT HUP INT TERM
fi
if [ -n "${JAVA_HOME:-}" ]; then
    JAVA="$JAVA_HOME/bin/java"
else
    JAVA=java
fi
exec "$JAVA" -cp "$JAR" org.gradle.wrapper.GradleWrapperMain "$@"
