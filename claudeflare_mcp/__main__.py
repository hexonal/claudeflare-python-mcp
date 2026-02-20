#!/usr/bin/env python3
"""
Cloudflare MCP Server 主入口点。
Cloudflare MCP Server main entry point.
"""

import sys


def main() -> None:
    """
    MCP 服务器启动入口，含错误处理。
    MCP server startup entry point with error handling.
    """
    try:
        print("Starting Cloudflare FastMCP Server...", file=sys.stderr)

        from . import mcp

        mcp.run()

    except KeyboardInterrupt:
        print("服务器已停止", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"启动服务器时发生错误: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
