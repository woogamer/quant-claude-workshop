#!/bin/bash
# 워크샵 초기 셋업 스크립트 — config.yaml 만 만들어줍니다.
# Codespace 부팅 시 requirements / Claude Code 는 devcontainer 가 처리합니다.

set -e

cd "$(dirname "$0")"

if [ -f config.yaml ]; then
  echo "config.yaml 이미 존재합니다."
  echo "다시 만들려면 'rm config.yaml' 후 재실행하세요."
  exit 0
fi

echo "==============================================="
echo " KIS 모의투자 키 입력 (한 번만 진행)"
echo " 발급: https://apiportal.koreainvestment.com/"
echo "==============================================="
echo

read -p "KIS App Key:         " APP_KEY
read -s -p "KIS App Secret:      " APP_SECRET; echo
read -p "계좌번호 (예 50012345-01): " ACCOUNT

read -p "DART API Key (선택, 엔터로 스킵): " DART_KEY

cat > config.yaml <<EOF
kis:
  app_key: "$APP_KEY"
  app_secret: "$APP_SECRET"
  account_no: "$ACCOUNT"

dart:
  api_key: "${DART_KEY:-YOUR_DART_API_KEY_HERE}"
EOF

chmod 600 config.yaml
echo
echo "config.yaml 생성 완료."
echo "이제 'claude' 명령으로 시작하세요."
