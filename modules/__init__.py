# table-tools 功能模块包

import ssl
import sys

# Python 3.14+ 移除了 ssl.OPENSSL_VERSION，但 urllib3 旧版本仍引用它
# 添加兼容性 shim 确保 requests/urllib3 在后台线程中也能正常导入
if sys.version_info >= (3, 14) and not hasattr(ssl, "OPENSSL_VERSION"):
    # 模拟 OpenSSL 版本字符串，避免 urllib3 旧版本导入时崩溃
    try:
        openssl_ver = ssl.OPENSSL_VERSION_INFO  # (major, minor, fix, patch, status)
        ssl.OPENSSL_VERSION = f"OpenSSL {'.'.join(str(v) for v in openssl_ver[:3])}"
    except AttributeError:
        ssl.OPENSSL_VERSION = "OpenSSL 3.x"
