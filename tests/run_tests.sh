#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
javac -encoding UTF-8 -d "$TMP" app/src/main/java/jp/example/dopagaki/GameSession.java tests/GameSessionTest.java
java -cp "$TMP" GameSessionTest
node tests/test_web.js
node --check web-demo/game-engine.js
sed -n '/^<script>$/,/^<\/script>$/p' web-demo/index.html | sed '1d;$d' > "$TMP/app-inline.js"
node --check "$TMP/app-inline.js"
echo "Android-independent logic and web demo syntax checks PASSED"
