#!/bin/bash
# OAuth 授权 + 订单 API 一键测试脚本
BASE="http://127.0.0.1:8001"

echo "=== 1. 授权获取 code ==="
CODE=$(curl -s -D- -o/dev/null -X POST "$BASE/oauth/authorize" \
  -d "client_id=order-client&redirect_uri=http://127.0.0.1:8001/docs&scope=orders:read+orders:write&state=test&action=approve" \
  | grep -i "^location:" | sed -n 's/.*code=\([^&]*\).*/\1/p' | tr -d '\r')
echo "Code: ${CODE:0:20}..."

echo ""
echo "=== 2. code 换 token ==="
TOKEN_RESP=$(curl -s -X POST "$BASE/oauth/token" \
  -d "grant_type=authorization_code&code=$CODE&redirect_uri=http://127.0.0.1:8001/docs&client_id=order-client&client_secret=order-secret")
echo "$TOKEN_RESP" | python3 -m json.tool
AT=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
RT=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['refresh_token'])")
echo ""
echo "Access Token:  ${AT:0:20}..."
echo "Refresh Token: ${RT:0:20}..."

echo ""
echo "=== 3. 创建订单 ==="
curl -s -X POST "$BASE/orders" \
  -H "Authorization: Bearer $AT" \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"测试用户","items":[{"name":"商品A","quantity":2,"unit_price":99.9}]}' | python3 -m json.tool

echo ""
echo "=== 4. 列出订单 ==="
curl -s "$BASE/orders" -H "Authorization: Bearer $AT" | python3 -m json.tool

echo ""
echo "=== 5. 无 token（401）==="
curl -s -w "\nHTTP %{http_code}" "$BASE/orders"

echo ""
echo ""
echo "=== 6. refresh token 续期 ==="
curl -s -X POST "$BASE/oauth/token" \
  -d "grant_type=refresh_token&refresh_token=$RT&client_id=order-client&client_secret=order-secret" | python3 -m json.tool

echo ""
echo "=== Done ==="
