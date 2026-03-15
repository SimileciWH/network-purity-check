# network-purity-check

`network-purity-check` 是一个基于 **Python 3.11** 的命令行工具，用于评估当前网络环境是否适合 Claude 自动化场景（分数越高代表风险越低）。

## 1. 功能概览

执行一次检测会输出：

- 公网 IP（多源多数决）
- IP 所属国家与 ASN
- ASN 类型（residential/datacenter/unknown）
- IP 信誉分（可选 APIVoid）
- DNS 泄漏检测（国家一致性）
- WebRTC/STUN 探测
- 多源 IP 一致性
- 最终 `purity_score` 与 `status`

## 2. 依赖关系

### 2.1 运行时依赖

- Python 3.11（必须）
- 标准库（内置，无需安装第三方包）
  - `argparse`
  - `urllib`
  - `socket`
  - `json`
  - `dataclasses`
  - `ipaddress`

### 2.2 外部网络依赖（检测时访问）

- Public IP:
  - `https://api.ipify.org`
  - `https://ifconfig.me/ip`
  - `https://ipinfo.io/ip`
- Metadata / Country:
  - `https://ipinfo.io/{ip}/json`
  - `https://ipinfo.io/{ip}/country`
- DNS 检测:
  - `resolver1.opendns.com:53`（UDP）
- WebRTC/STUN:
  - `stun.l.google.com:19302`（UDP）
- Reputation（可选）:
  - `https://endpoint.apivoid.com/...`（需要 `APIVOID_API_KEY`）

## 3. 基本运行要求

要让脚本稳定工作，建议满足以下条件：

1. 本机可使用 `python3.11` 命令。
2. 出口网络允许访问上述 HTTPS/UDP 目标。
3. 如果启用代理，需确认代理不会阻断 UDP（否则 DNS/STUN 可能超时）。
4. 若使用信誉查询，需设置环境变量：
   - `APIVOID_API_KEY=<your_key>`

## 4. 快速开始

在项目根目录执行：

```bash
./network-purity-check run
./network-purity-check run --json
./network-purity-check run --verbose --timeout 8
```

等价入口：

```bash
python3.11 -m network_purity_check.cli run --json
```

## 5. 命令行参数

- `run`：执行检测
- `--json`：JSON 输出
- `--verbose`：显示调试信息
- `--timeout`：请求超时（秒，默认 `5`）

## 6. 评分与策略

当前评分针对 Claude 风险场景，关键项高权重：

- `claude_supported=false`：高惩罚
- `ip_consistency=false`：高惩罚
- `country_mismatch=true`：高惩罚
- `dns_check_ok=false` / `webrtc_check_ok=false`：检测失败也惩罚

可选地区白名单覆盖：

```bash
export CLAUDE_ALLOWED_COUNTRIES="US,JP,SG,TW"
```

## 7. 输出字段说明（JSON）

- `ip`: 公网 IP
- `country`: IP 所在国家
- `target`: 风险目标（当前为 `claude`）
- `claude_supported`: 是否在策略允许地区
- `asn` / `asn_type`: ASN 及其类型
- `fraud_score`: 信誉分
- `dns_country` / `dns_check_ok`: DNS 结果与检测是否成功
- `webrtc_leak` / `webrtc_check_ok`: WebRTC 结果与检测是否成功
- `ip_consistency`: 多源 IP 是否一致
- `purity_score`: 风险分
- `status`: `clean` / `acceptable` / `risky`

## 8. 安全与隐私说明

- 项目代码中不应存储你的密钥、账号、手机号、真实地址等隐私信息。
- API Key 仅通过环境变量读取，不写入代码。
- 建议在 CI/CD 和本地使用密钥管理，不要提交到仓库。
