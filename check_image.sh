#!/bin/sh
# 直接验证麦麦绘卷当前配置的 NewAPI gpt-image-2 文生图请求。
# 注意：成功时会实际生成图片，可能消耗服务商额度。

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
config_file="$script_dir/runtime/data/MaiMBot/plugins/1021143806_mais_art_journal/config.toml"
model_id="gpt-image-2"

if [ ! -r "$config_file" ]; then
    printf '%s\n' "错误：找不到或无法读取绘卷配置：$config_file" >&2
    exit 2
fi

if ! command -v curl >/dev/null 2>&1; then
    printf '%s\n' '错误：未找到 curl。请先安装 curl 后重试。' >&2
    exit 2
fi

# 只取目标模型段的 api_key；绝不向终端输出密钥。
api_key=$(awk -v target="$model_id" '
function value(line) {
    sub(/^[^=]*=/, "", line)
    gsub(/^[ \t]+|[ \t]+$/, "", line)
    if (line ~ /^".*"$/) {
        sub(/^"/, "", line)
        sub(/"$/, "", line)
    }
    return line
}
/^\[\[models\.items\]\]/ {
    if (in_model && id == target && key != "") {
        print key
        printed = 1
        exit
    }
    in_model = 1
    id = ""
    key = ""
    next
}
in_model && /^[ \t]*id[ \t]*=/ { id = value($0); next }
in_model && /^[ \t]*api_key[ \t]*=/ { key = value($0); next }
END {
    if (!printed && in_model && id == target && key != "") {
        print key
    }
}
' "$config_file")

if [ -z "$api_key" ]; then
    printf '%s\n' "错误：未在绘卷配置中找到模型 $model_id 的 API Key。" >&2
    exit 2
fi

case "$api_key" in
    'Bearer '*) ;;
    *)
        printf '%s\n' '错误：API Key 未以 "Bearer " 开头；为避免无效请求，已取消。' >&2
        exit 2
        ;;
esac

response_dir=$(mktemp -d "${TMPDIR:-/tmp}/maibot-image-check.XXXXXX")
trap 'rm -rf "$response_dir"; unset api_key' EXIT HUP INT TERM

printf '%s\n' "测试 NewAPI 的 $model_id 文生图接口（成功会消耗额度）..." >&2

set +e
http_status=$(curl -sS --noproxy '*' --connect-timeout 15 --max-time 120 \
    -D "$response_dir/headers" \
    -o "$response_dir/body" \
    -w '%{http_code}' \
    -X POST 'https://yyds.chybenzun.top/v1/images/generations' \
    -H "Authorization: $api_key" \
    -H 'Content-Type: application/json' \
    --data '{"model":"gpt-image-2","prompt":"A simple blue circle on a white background","n":1,"size":"1024x1024","quality":"low","output_format":"png","response_format":"url"}')
curl_status=$?
set -e

printf '%s\n' '--- 响应头 ---'
sed -n '1,80p' "$response_dir/headers"
printf '%s\n' '--- 响应正文 ---'
sed -n '1,200p' "$response_dir/body"
printf '\nHTTP 状态：%s\n' "${http_status:-无响应}"

if [ "$curl_status" -ne 0 ]; then
    printf 'curl 失败，退出码：%s\n' "$curl_status" >&2
    exit "$curl_status"
fi

case "$http_status" in
    2??)
        printf '%s\n' '测试成功：网关、认证和该模型的文生图权限均正常。'
        ;;
    *)
        printf '%s\n' '测试失败：请根据上方响应正文判断服务商的具体拒绝原因。' >&2
        exit 1
        ;;
esac
