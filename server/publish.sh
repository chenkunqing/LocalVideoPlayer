#!/bin/bash
# 一键发版：打包 → 生成 latest.json → 上传到服务器

set -e

SERVER_USER="root"
SERVER_IP="119.91.95.23"
SERVER_DIR="~/kkplayer/server/releases"

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RELEASES_DIR="$(dirname "$0")/releases"

# 1. 自动从 git log 提取更新说明（上次发版到现在的所有 commit）
PREV_VERSION=$(python -c "import json; print(json.load(open('$RELEASES_DIR/latest.json'))['version'])" 2>/dev/null || echo "")
if [ -n "$PREV_VERSION" ] && git rev-parse "$PREV_VERSION" >/dev/null 2>&1; then
    CHANGELOG=$(git log "${PREV_VERSION}..HEAD" --pretty=format:"- %s" --no-merges)
else
    CHANGELOG=$(git log -10 --pretty=format:"- %s" --no-merges)
fi
echo "更新说明："
echo "$CHANGELOG"
echo ""
read -r -p "回车确认，或输入自定义说明: " CUSTOM
CHANGELOG="${CUSTOM:-$CHANGELOG}"

# 2. 打包
echo "正在打包..."
cd "$PROJECT_ROOT"
python -m PyInstaller build.spec --noconfirm

# 3. 读取版本号
VERSION=$(cat "$PROJECT_ROOT/src/VERSION")

# 4. 复制 exe 到本地 releases
cp "$PROJECT_ROOT/dist/KKPlayer.exe" "$RELEASES_DIR/KKPlayer.exe"

# 5. 获取文件大小
FILE_SIZE=$(stat -c%s "$RELEASES_DIR/KKPlayer.exe" 2>/dev/null || stat -f%z "$RELEASES_DIR/KKPlayer.exe")
SIZE_MB=$((FILE_SIZE / 1024 / 1024))

# 6. 生成 latest.json（用 python 确保 JSON 合法）
python -c "
import json
data = {
    'version': '$VERSION',
    'download_url': 'http://${SERVER_IP}:3002/releases/KKPlayer.exe',
    'changelog': '''$CHANGELOG''',
    'file_size': $FILE_SIZE,
}
with open('$RELEASES_DIR/latest.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
"

echo ""
echo "打包完成: v${VERSION}, ${SIZE_MB}MB"
echo "更新说明: ${CHANGELOG}"

# 7. 上传到服务器
echo "正在上传到服务器..."
scp "$RELEASES_DIR/KKPlayer.exe" "${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/KKPlayer.exe"
scp "$RELEASES_DIR/latest.json" "${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/latest.json"

echo ""
echo "发版完成！客户端可以检查更新了。"
