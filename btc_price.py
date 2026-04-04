import requests
import time
from datetime import datetime

# Binance 镜像节点，国内可直连，无需 API Key
BASE_URL = "https://data-api.binance.vision/api/v3"
SYMBOL = "BTCUSDT"


def get_btc_price() -> float:
    resp = requests.get(f"{BASE_URL}/ticker/price", params={"symbol": SYMBOL}, timeout=10)
    resp.raise_for_status()
    return float(resp.json()["price"])


def get_stats() -> dict:
    resp = requests.get(f"{BASE_URL}/ticker/24hr", params={"symbol": SYMBOL}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "price":      float(data["lastPrice"]),
        "change":     float(data["priceChange"]),
        "change_pct": float(data["priceChangePercent"]),
        "high":       float(data["highPrice"]),
        "low":        float(data["lowPrice"]),
        "volume":     float(data["volume"]),
        "quote_vol":  float(data["quoteVolume"]),
    }


def print_row(stats: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    arrow = "▲" if stats["change"] >= 0 else "▼"
    print(
        f"[{now}]  BTC/USDT: ${stats['price']:>12,.2f}  "
        f"{arrow} {stats['change_pct']:>+.2f}%   "
        f"24h高: ${stats['high']:>12,.2f}  "
        f"24h低: ${stats['low']:>12,.2f}  "
        f"成交量: {stats['volume']:>10,.2f} BTC"
    )


def monitor(interval: int = 10):
    print(f"实时监控 BTC/USDT（每 {interval} 秒刷新，Ctrl+C 退出）\n")
    print("-" * 115)
    while True:
        try:
            print_row(get_stats())
        except requests.exceptions.Timeout:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 请求超时，稍后重试...")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 错误: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    try:
        stats = get_stats()
    except Exception as e:
        print(f"查询失败: {e}")
        exit(1)

    print(f"BTC/USDT 当前价格: ${stats['price']:,.2f} USDT\n")
    print("===== 24 小时统计 =====")
    print(f"  当前价格 : ${stats['price']:>12,.2f} USDT")
    print(f"  涨跌幅   : {stats['change_pct']:>+.2f}%  ({stats['change']:>+,.2f} USDT)")
    print(f"  24h 最高 : ${stats['high']:>12,.2f} USDT")
    print(f"  24h 最低 : ${stats['low']:>12,.2f} USDT")
    print(f"  成交量   : {stats['volume']:>12,.2f} BTC")
    print(f"  成交额   : ${stats['quote_vol']:>16,.2f} USDT\n")

    try:
        monitor(interval=10)
    except KeyboardInterrupt:
        print("\n已退出监控。")
