#!/bin/bash
# ============================================
# Tiresias 맥미니 서버 자동 세팅 스크립트
# 맥미니에서 실행: bash setup-macmini.sh
# ============================================

set -e

echo "========================================="
echo "  Tiresias 맥미니 서버 세팅 시작"
echo "========================================="

# 사용자 홈 디렉토리
HOME_DIR="$HOME"
PROJECT_DIR="$HOME_DIR/tiresias"
BACKEND_DIR="$PROJECT_DIR/backend"

# ─── 1. Homebrew 설치 ───
if ! command -v brew &>/dev/null; then
  echo "[1/7] Homebrew 설치 중..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME_DIR/.zprofile"
  eval "$(/opt/homebrew/bin/brew shellenv)"
else
  echo "[1/7] Homebrew 이미 설치됨 ✓"
fi

# ─── 2. cloudflared 설치 ───
if ! command -v cloudflared &>/dev/null; then
  echo "[2/7] cloudflared 설치 중..."
  brew install cloudflared
else
  echo "[2/7] cloudflared 이미 설치됨 ✓"
fi

# ─── 3. uv 설치 ───
if ! command -v uv &>/dev/null; then
  echo "[3/7] uv 설치 중..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME_DIR/.local/bin:$PATH"
else
  echo "[3/7] uv 이미 설치됨 ✓"
fi

# ─── 4. Python 3.12 설치 ───
echo "[4/7] Python 3.12 설치 중..."
uv python install 3.12

# ─── 5. 프로젝트 복사 확인 ───
if [ ! -d "$BACKEND_DIR" ]; then
  echo ""
  echo "⚠️  프로젝트가 $PROJECT_DIR 에 없습니다."
  echo "   맥북에서 다음 명령어로 복사하세요:"
  echo ""
  echo "   scp -r /Users/mavenworks/workspace/mirofish/backend USER@MACMINI_IP:~/tiresias/backend"
  echo "   scp /Users/mavenworks/workspace/mirofish/.env USER@MACMINI_IP:~/tiresias/.env"
  echo ""
  echo "   복사 후 이 스크립트를 다시 실행하세요."
  exit 1
fi

# ─── 6. 백엔드 의존성 설치 ───
echo "[5/7] 백엔드 의존성 설치 중..."
cd "$BACKEND_DIR"
uv sync

# ─── 6. Cloudflare 터널 설정 ───
echo "[6/7] Cloudflare 터널 설정..."
if ! cloudflared tunnel list 2>/dev/null | grep -q "tiresias-backend"; then
  echo "  Cloudflare 로그인이 필요합니다."
  cloudflared tunnel login
  cloudflared tunnel create tiresias-backend
  echo "  터널 생성 완료 ✓"
else
  echo "  터널 이미 존재함 ✓"
fi

# 터널 ID 가져오기
TUNNEL_ID=$(cloudflared tunnel list 2>/dev/null | grep "tiresias-backend" | awk '{print $1}')
echo "  터널 ID: $TUNNEL_ID"

# ─── 7. LaunchAgent 등록 (자동 실행) ───
echo "[7/7] 자동 실행 서비스 등록 중..."

LAUNCH_DIR="$HOME_DIR/Library/LaunchAgents"
mkdir -p "$LAUNCH_DIR"

UV_PATH=$(which uv)
CLOUDFLARED_PATH=$(which cloudflared)

# Flask 백엔드 서비스
cat > "$LAUNCH_DIR/com.tiresias.backend.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tiresias.backend</string>
    <key>WorkingDirectory</key>
    <string>$BACKEND_DIR</string>
    <key>ProgramArguments</key>
    <array>
        <string>$UV_PATH</string>
        <string>run</string>
        <string>python</string>
        <string>run.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME_DIR/tiresias/logs/backend.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME_DIR/tiresias/logs/backend-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$HOME_DIR/.local/bin</string>
        <key>DOTENV_PATH</key>
        <string>$PROJECT_DIR/.env</string>
    </dict>
</dict>
</plist>
PLIST

# Cloudflare 터널 서비스
cat > "$LAUNCH_DIR/com.tiresias.tunnel.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tiresias.tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>$CLOUDFLARED_PATH</string>
        <string>tunnel</string>
        <string>run</string>
        <string>--url</string>
        <string>http://localhost:5001</string>
        <string>tiresias-backend</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME_DIR/tiresias/logs/tunnel.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME_DIR/tiresias/logs/tunnel-error.log</string>
</dict>
</plist>
PLIST

# 로그 디렉토리 생성
mkdir -p "$HOME_DIR/tiresias/logs"

# 서비스 시작
launchctl unload "$LAUNCH_DIR/com.tiresias.backend.plist" 2>/dev/null || true
launchctl unload "$LAUNCH_DIR/com.tiresias.tunnel.plist" 2>/dev/null || true
launchctl load "$LAUNCH_DIR/com.tiresias.backend.plist"
launchctl load "$LAUNCH_DIR/com.tiresias.tunnel.plist"

echo ""
echo "========================================="
echo "  세팅 완료!"
echo "========================================="
echo ""
echo "  Flask 백엔드: http://localhost:5001"
echo "  터널 URL 확인: cloudflared tunnel info tiresias-backend"
echo ""
echo "  로그 확인:"
echo "    tail -f ~/tiresias/logs/backend.log"
echo "    tail -f ~/tiresias/logs/tunnel.log"
echo ""
echo "  서비스 상태:"
echo "    launchctl list | grep tiresias"
echo ""
echo "  ⚠️ 터널 URL을 CF Worker에 등록하세요:"
echo "    cd workers && npx wrangler secret put SIMULATION_API"
echo "    → 터널 URL 입력 (https://xxx.cfargotunnel.com)"
echo ""
