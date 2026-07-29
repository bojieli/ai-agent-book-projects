"""
用于日志脱敏演示的代表性样本

这些样本模拟真实 Agent 运行时最容易泄露敏感信息的几种场景：
工具调用的 HTTP 请求/响应、客服对话、数据库连接报错、CI/Git 日志、
以及配置转储。它们混合了密钥类（API Key、令牌、私钥）与 PII 类
（身份证、手机号、信用卡、邮箱）敏感信息，便于展示脱敏的覆盖面。

注意：以下所有密钥、卡号、证件号均为虚构，仅用于演示，不对应任何真实账户。
"""

SAMPLES = [
    (
        "工具调用日志 (HTTP 请求/响应)",
        """[2024-05-12 09:14:22] TOOL_CALL http_request
  url: https://api.example.com/v1/users/8842
  headers: {"Authorization": "Bearer sk-proj-ABCD1234efgh5678IJKL9012mnop3456qrst", "X-Api-Key": "AIzaSyD-EXAMPLEfakeKEY1234567890abcdef12"}
  response: {"user_id": 8842, "email": "alice.wang@example.com", "phone": "13912345678"}""",
    ),
    (
        "客服对话 (PII 泄露)",
        """USER: 你好，我要办理报销，我的身份证号是 11010119900307721X，手机号 13800138000。
ASSISTANT: 好的，请再提供一下银行卡号以便核对。
USER: 卡号是 4111 1111 1111 1111，另外我的美国社保号是 123-45-6789。
ASSISTANT: 收到，我这就为您登记。""",
    ),
    (
        "数据库连接报错 (凭据泄露)",
        """[ERROR] db.connect failed after 3 retries
  dsn: postgres://admin:S3cr3t_P4ssw0rd@db.internal:5432/prod
  fallback_config: {"db_password": "hunter2xyz", "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE"}
  host_ip: 192.168.10.24""",
    ),
    (
        "CI / Git 日志 (令牌泄露)",
        """Cloning into 'service-repo'...
  remote: using deploy token ghp_16C7e42F292c6912E7710c838347Ae178B4a99
  Slack notify webhook token: xoxb-PLACEHOLDERfaketoken000000notarealslacktoken
  session jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c""",
    ),
    (
        "配置转储 (私钥泄露)",
        """[DEBUG] dumping runtime config
  service_account_key: |
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA7QwZbq3vX9kLmN0pQrStUvWxYz1234567890abcdefghijkl
mnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0987654321zyxwvutsrqponm
QIDAQAB
-----END RSA PRIVATE KEY-----
  admin_contact: ops-team@example.com""",
    ),
]
