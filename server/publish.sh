#!/bin/bash
# 一键发版：递增版本号 → 打包 → 生成补丁 → 上传到服务器

set -e

SERVER_USER="root"
SERVER_IP="119.91.95.23"
SERVER_DIR="~/kkplayer/server/releases"

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RELEASES_DIR="$(dirname "$0")/releases"
VERSION_FILE="$PROJECT_ROOT/src/VERSION"

# Python 需要 Windows 格式路径
WIN_PROJECT_ROOT="$(cygpath -w "$PROJECT_ROOT")"
WIN_RELEASES_DIR="$(cygpath -w "$RELEASES_DIR")"

# 1. 版本号递增（当前版本 +0.0.1）
PREV_VERSION=$(cat "$VERSION_FILE")
VERSION=$(python -c "
v = '$PREV_VERSION'.split('.')
v[2] = str(int(v[2]) + 1)
print('.'.join(v))
")
echo "版本: $PREV_VERSION → $VERSION"
read -r -p "回车确认，或输入自定义版本号（如 2.0.0）: " CUSTOM_VER
VERSION="${CUSTOM_VER:-$VERSION}"
echo "$VERSION" > "$VERSION_FILE"

# 2. 更新说明（从 git log 提取）
CHANGELOG=$(git log --pretty=format:"- %s" --no-merges -10)
echo ""
echo "更新说明："
echo "$CHANGELOG"
echo ""
read -r -p "回车确认，或输入自定义说明: " CUSTOM
CHANGELOG="${CUSTOM:-$CHANGELOG}"

# 3. 打包
echo "正在打包..."
cd "$PROJECT_ROOT"
python -m PyInstaller build.spec --noconfirm

# 4. 生成增量补丁（用本地上次发版的 exe 对比）
PATCH_URL=""
PATCH_SIZE=0
OLD_EXE="$RELEASES_DIR/KKPlayer.exe"

if [ -f "$OLD_EXE" ]; then
    echo "正在生成增量补丁..."
    WIN_OLD_EXE="$(cygpath -w "$OLD_EXE")"
    python -c "
import bsdiff4
old = open(r'$WIN_OLD_EXE', 'rb').read()
new = open(r'$WIN_PROJECT_ROOT\\dist\\KKPlayer.exe', 'rb').read()
patch = bsdiff4.diff(old, new)
with open(r'$WIN_RELEASES_DIR\\patch.bin', 'wb') as f:
    f.write(patch)
print(f'补丁大小: {len(patch) / 1024 / 1024:.1f} MB')
"
    PATCH_SIZE=$(stat -c%s "$RELEASES_DIR/patch.bin" 2>/dev/null || stat -f%z "$RELEASES_DIR/patch.bin")
    PATCH_URL="http://${SERVER_IP}:3002/releases/patch.bin"
else
    echo "本地无旧版 exe，跳过增量补丁（首次发版）"
fi

# 5. 用新 exe 覆盖本地旧版（下次发版对比用）
cp "$PROJECT_ROOT/dist/KKPlayer.exe" "$RELEASES_DIR/KKPlayer.exe"

# 6. 获取文件大小
FILE_SIZE=$(stat -c%s "$RELEASES_DIR/KKPlayer.exe" 2>/dev/null || stat -f%z "$RELEASES_DIR/KKPlayer.exe")
SIZE_MB=$((FILE_SIZE / 1024 / 1024))

# 7. 生成 latest.json（用 base64 传 changelog 避免特殊字符破坏语法）
CHANGELOG_B64=$(echo "$CHANGELOG" | python -c "import sys,base64; print(base64.b64encode(sys.stdin.buffer.read()).decode())")
python -c "
import json, base64
changelog = base64.b64decode('$CHANGELOG_B64').decode('utf-8').strip()
data = {
    'version': '$VERSION',
    'download_url': 'http://${SERVER_IP}:3002/releases/KKPlayer.exe',
    'changelog': changelog,
    'file_size': $FILE_SIZE,
    'patch_url': '$PATCH_URL' or None,
    'patch_size': $PATCH_SIZE or None,
    'prev_version': '$PREV_VERSION' or None,
}
data = {k: v for k, v in data.items() if v is not None}
with open(r'$WIN_RELEASES_DIR\\latest.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
"

echo ""
echo "发版完成: v${VERSION}, ${SIZE_MB}MB"
if [ -n "$PATCH_URL" ]; then
    echo "增量补丁: $((PATCH_SIZE / 1024))KB"
fi

# 8. 上传到服务器
echo "正在上传到服务器..."
scp "$RELEASES_DIR/KKPlayer.exe" "${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/KKPlayer.exe"
scp "$RELEASES_DIR/latest.json" "${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/latest.json"
if [ -f "$RELEASES_DIR/patch.bin" ]; then
    scp "$RELEASES_DIR/patch.bin" "${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/patch.bin"
fi

# 9. 提交版本号变更到 git
cd "$PROJECT_ROOT"
git add src/VERSION
git commit -m "release: v${VERSION}" || true

echo ""
echo "全部完成！客户端可以检查更新了。"
