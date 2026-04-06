import pandas as pd
import requests
import os
import logging
from datetime import datetime, timedelta
import yfinance as yf
import json
import re

# 配置日志记录
logging.basicConfig(
    filename='repo_flow.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fetch_treasury_2y_data():
    """
    从多个网络数据源获取美国2年期国债收益率 (2Y)
    如果当天数据获取不到，会自动回溯到前几天的数据
    优先级：Trading Economics > 美联储 > Treasury Direct > yfinance > 本地参考数据
    """
    # 尝试回溯最多7天的数据
    for days_back in range(8):  # 0-7天
        target_date = datetime.now().date() - timedelta(days=days_back)
        target_date_str = target_date.strftime('%Y-%m-%d')

        # 跳过周末（周六日通常没有交易数据）
        if target_date.weekday() >= 5:  # 5=周六, 6=周日
            continue

        logging.info(f"尝试获取 {target_date_str} 的 2Y 国债收益率...")

        # 尝试方案 1：从 Trading Economics 获取 (最准确)
        try:
            url = "https://tradingeconomics.com/united-states/2-year-note-yield"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                patterns = [
                    r'"value"["\s:]*(\d+\.\d{2,4})',  # JSON 格式的 value 字段
                    r'yield.*?rose.*?to\s*(\d+\.\d{2,3})',  # 描述格式
                    r'US 2.*?Bond Yield.*?(\d+\.\d{2,3})\s*%',  # 标题格式
                    r'last[:=\s]*(\d+\.\d{2,4})',  # last 字段
                ]

                for pattern in patterns:
                    match = re.search(pattern, response.text, re.IGNORECASE | re.DOTALL)
                    if match:
                        value = float(match.group(1))
                        # 确保数值在合理范围内 (2Y国债收益率通常在 0.1% - 8% 之间)
                        if 0.1 < value < 8:
                            logging.info(f"✅ 成功从 Trading Economics 获取 {target_date_str} 的 2Y: {value}%")
                            return {
                                'date': pd.to_datetime(target_date),
                                'value': value,
                                'description': f'2Y 国债收益率 ({target_date_str})'
                            }
        except Exception as e:
            logging.warning(f"从 Trading Economics 获取 {target_date_str} 的 2Y 失败: {e}")

        # 尝试方案 2：从 yfinance 获取 (使用历史数据)
        try:
            logging.info(f"尝试从 yfinance 获取 {target_date_str} 的 2Y 国债收益率...")
            # 2Y国债的ticker是^TWO
            two = yf.Ticker("^TWO")
            # 获取最近5天的数据，确保包含目标日期
            hist = two.history(start=target_date - timedelta(days=2), end=target_date + timedelta(days=1))

            if hist is not None and len(hist) > 0:
                # 查找最接近目标日期的数据
                hist.index = hist.index.date
                if target_date in hist.index:
                    value = hist.loc[target_date, 'Close']
                    logging.info(f"✅ 成功从 yfinance 获取 {target_date_str} 的 2Y: {value}%")
                    return {
                        'date': pd.to_datetime(target_date),
                        'value': value,
                        'description': f'2Y 国债收益率 ({target_date_str})'
                    }
                else:
                    # 如果没有精确匹配，找最近的交易日
                    available_dates = [d for d in hist.index if d <= target_date]
                    if available_dates:
                        closest_date = max(available_dates)
                        value = hist.loc[closest_date, 'Close']
                        actual_date_str = closest_date.strftime('%Y-%m-%d')
                        logging.info(f"✅ 成功从 yfinance 获取 {actual_date_str} 的 2Y: {value}% (最接近 {target_date_str})")
                        return {
                            'date': pd.to_datetime(closest_date),
                            'value': value,
                            'description': f'2Y 国债收益率 ({actual_date_str})'
                        }
        except Exception as e:
            logging.warning(f"从 yfinance 获取 {target_date_str} 的 2Y 失败: {e}")

# 如果所有网络获取都失败，返回None
    logging.error("无法从任何网络来源获取 2Y 国债收益率")
    return None

def fetch_treasury_data():
    """
    从多个网络数据源获取美国10年期国债收益率 (10Y TNX)
    如果当天数据获取不到，会自动回溯到前几天的数据
    优先级：Trading Economics > 美联储 > Treasury Direct > yfinance > 本地参考数据
    """
    # 尝试回溯最多7天的数据
    for days_back in range(8):  # 0-7天
        target_date = datetime.now().date() - timedelta(days=days_back)
        target_date_str = target_date.strftime('%Y-%m-%d')

        # 跳过周末（周六日通常没有交易数据）
        if target_date.weekday() >= 5:  # 5=周六, 6=周日
            continue

        logging.info(f"尝试获取 {target_date_str} 的 10Y 国债收益率...")

        # 尝试方案 1：从 Trading Economics 获取 (最准确)
        try:
            url = "https://tradingeconomics.com/united-states/government-bond-yield"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                patterns = [
                    r'"value"["\s:]*(\d+\.\d{2,4})',  # JSON 格式的 value 字段
                    r'yield.*?rose.*?to\s*(\d+\.\d{2,3})',  # 描述格式
                    r'US 10.*?Bond Yield.*?(\d+\.\d{2,3})\s*%',  # 标题格式
                    r'last[:=\s]*(\d+\.\d{2,4})',  # last 字段
                ]

                for pattern in patterns:
                    match = re.search(pattern, response.text, re.IGNORECASE | re.DOTALL)
                    if match:
                        value = float(match.group(1))
                        # 确保数值在合理范围内 (国债收益率通常在 0.1% - 10% 之间)
                        if 0.1 < value < 10:
                            logging.info(f"✅ 成功从 Trading Economics 获取 {target_date_str} 的 10Y: {value}%")
                            return {
                                'date': pd.to_datetime(target_date),
                                'value': value,
                                'description': f'10Y 国债收益率 ({target_date_str})'
                            }
        except Exception as e:
            logging.warning(f"从 Trading Economics 获取 {target_date_str} 的 10Y 失败: {e}")

        # 尝试方案 2：从 yfinance 获取 (使用历史数据)
        try:
            logging.info(f"尝试从 yfinance 获取 {target_date_str} 的 10Y 国债收益率...")
            tnx = yf.Ticker("^TNX")
            # 获取最近5天的数据，确保包含目标日期
            hist = tnx.history(start=target_date - timedelta(days=2), end=target_date + timedelta(days=1))

            if hist is not None and len(hist) > 0:
                # 查找最接近目标日期的数据
                hist.index = hist.index.date
                if target_date in hist.index:
                    value = hist.loc[target_date, 'Close']
                    logging.info(f"✅ 成功从 yfinance 获取 {target_date_str} 的 10Y: {value}%")
                    return {
                        'date': pd.to_datetime(target_date),
                        'value': value,
                        'description': f'10Y 国债收益率 ({target_date_str})'
                    }
                else:
                    # 如果没有精确匹配，找最近的交易日
                    available_dates = [d for d in hist.index if d <= target_date]
                    if available_dates:
                        closest_date = max(available_dates)
                        value = hist.loc[closest_date, 'Close']
                        actual_date_str = closest_date.strftime('%Y-%m-%d')
                        logging.info(f"✅ 成功从 yfinance 获取 {actual_date_str} 的 10Y: {value}% (最接近 {target_date_str})")
                        return {
                            'date': pd.to_datetime(closest_date),
                            'value': value,
                            'description': f'10Y 国债收益率 ({actual_date_str})'
                        }
        except Exception as e:
            logging.warning(f"从 yfinance 获取 {target_date_str} 的 10Y 失败: {e}")

# 如果所有网络获取都失败，返回None
    logging.error("无法从任何网络来源获取 10Y 国债收益率")
    return None

def fetch_sofr_data():
    """
    从纽约联储官方API获取 SOFR (Secured Overnight Financing Rate)
    如果当天数据获取不到，会自动回溯到前几天的数据
    使用官方数据源：https://markets.newyorkfed.org/api/rates/secured/sofr/last/1.json
    """
    # 尝试回溯最多7天的数据
    for days_back in range(8):  # 0-7天
        target_date = datetime.now().date() - timedelta(days=days_back)
        target_date_str = target_date.strftime('%Y-%m-%d')

        # 跳过周末（周六日通常没有交易数据）
        if target_date.weekday() >= 5:  # 5=周六, 6=周日
            continue

        logging.info(f"尝试获取 {target_date_str} 的 SOFR 数据...")

        # 从纽约联储官方API获取数据
        try:
            url = "https://markets.newyorkfed.org/api/rates/secured/sofr/last/1.json"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json()

                # 解析API响应
                if 'refRates' in data and len(data['refRates']) > 0:
                    rate_data = data['refRates'][0]
                    effective_date = pd.to_datetime(rate_data['effectiveDate']).date()
                    sofr_value = rate_data['percentRate']

                    # 检查数据是否足够接近目标日期（允许1-2天的差异）
                    date_diff = abs((effective_date - target_date).days)
                    if date_diff <= 2:  # 如果数据日期与目标日期相差不超过2天
                        logging.info(f"✅ 成功从纽约联储获取 SOFR: {sofr_value}% (日期: {rate_data['effectiveDate']})")
                        return {
                            'date': pd.to_datetime(effective_date),
                            'value': sofr_value,
                            'description': f'SOFR 隔夜融资利率 ({rate_data["effectiveDate"]})'
                        }
                    else:
                        logging.info(f"API返回的数据日期 {rate_data['effectiveDate']} 与目标日期 {target_date_str} 相差 {date_diff} 天，尝试其他日期")

        except Exception as e:
            logging.warning(f"从纽约联储获取 {target_date_str} 的 SOFR 失败: {e}")

    # 如果所有网络获取都失败，返回None
    logging.error("无法从纽约联储获取 SOFR 数据")
    return None

def fetch_effr_data():
    """
    从纽约联储官方API获取 EFFR (Effective Federal Funds Rate)
    如果当天数据获取不到，会自动回溯到前几天的数据
    使用官方数据源：https://markets.newyorkfed.org/api/rates/unsecured/effr/last/1.json
    """
    # 尝试回溯最多7天的数据
    for days_back in range(8):  # 0-7天
        target_date = datetime.now().date() - timedelta(days=days_back)
        target_date_str = target_date.strftime('%Y-%m-%d')

        # 跳过周末（周六日通常没有交易数据）
        if target_date.weekday() >= 5:  # 5=周六, 6=周日
            continue

        logging.info(f"尝试获取 {target_date_str} 的 EFFR 数据...")

        # 从纽约联储官方API获取数据
        try:
            url = "https://markets.newyorkfed.org/api/rates/unsecured/effr/last/1.json"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json()

                # 解析API响应
                if 'refRates' in data and len(data['refRates']) > 0:
                    rate_data = data['refRates'][0]
                    effective_date = pd.to_datetime(rate_data['effectiveDate']).date()
                    effr_value = rate_data['percentRate']

                    # 检查数据是否足够接近目标日期（允许1-2天的差异）
                    date_diff = abs((effective_date - target_date).days)
                    if date_diff <= 2:  # 如果数据日期与目标日期相差不超过2天
                        logging.info(f"✅ 成功从纽约联储获取 EFFR: {effr_value}% (日期: {rate_data['effectiveDate']})")
                        return {
                            'date': pd.to_datetime(effective_date),
                            'value': effr_value,
                            'description': f'EFFR 实际联邦基金利率 ({rate_data["effectiveDate"]})'
                        }
                    else:
                        logging.info(f"API返回的数据日期 {rate_data['effectiveDate']} 与目标日期 {target_date_str} 相差 {date_diff} 天，尝试其他日期")

        except Exception as e:
            logging.warning(f"从纽约联储获取 {target_date_str} 的 EFFR 失败: {e}")

    # 如果所有网络获取都失败，返回None
    logging.error("无法从纽约联储获取 EFFR 数据")
    return None

def fetch_market_data():
    """
    从网络获取市场数据 (VIX 波动率指数)
    如果当天数据获取不到，会自动回溯到前几天的数据
    """
    # 尝试回溯最多7天的数据
    for days_back in range(8):  # 0-7天
        target_date = datetime.now().date() - timedelta(days=days_back)
        target_date_str = target_date.strftime('%Y-%m-%d')

        # 跳过周末（周六日通常没有交易数据）
        if target_date.weekday() >= 5:  # 5=周六, 6=周日
            continue

        logging.info(f"尝试获取 {target_date_str} 的 VIX 数据...")

        try:
            vix = yf.Ticker("^VIX")
            # 获取最近5天的数据，确保包含目标日期
            hist = vix.history(start=target_date - timedelta(days=2), end=target_date + timedelta(days=1))

            if hist is not None and len(hist) > 0:
                # 查找最接近目标日期的数据
                hist.index = hist.index.date
                if target_date in hist.index:
                    value = hist.loc[target_date, 'Close']
                    logging.info(f"✅ 成功从 yfinance 获取 {target_date_str} 的 VIX: {value}")
                    return {
                        'date': pd.to_datetime(target_date),
                        'value': value,
                        'description': f'VIX 波动率指数 ({target_date_str})'
                    }
                else:
                    # 如果没有精确匹配，找最近的交易日
                    available_dates = [d for d in hist.index if d <= target_date]
                    if available_dates:
                        closest_date = max(available_dates)
                        value = hist.loc[closest_date, 'Close']
                        actual_date_str = closest_date.strftime('%Y-%m-%d')
                        logging.info(f"✅ 成功从 yfinance 获取 {actual_date_str} 的 VIX: {value} (最接近 {target_date_str})")
                        return {
                            'date': pd.to_datetime(closest_date),
                            'value': value,
                            'description': f'VIX 波动率指数 ({actual_date_str})'
                        }
        except Exception as e:
            logging.warning(f"从 yfinance 获取 {target_date_str} 的 VIX 失败: {e}")

    # 如果所有网络获取都失败，返回None
    logging.error("无法从任何网络来源获取 VIX 数据")
    return None

def main():
    print(f"🚀 启动 2026 债务高墙监控任务... [{datetime.now()}]")
    print("   数据源：仅从网络获取，网络不可用时提示无法读取\n")

    # 获取所有数据 (仅从网络获取)
    treasury_2y_data = fetch_treasury_2y_data()
    treasury_data = fetch_treasury_data()
    market_data = fetch_market_data()
    sofr_data = fetch_sofr_data()
    effr_data = fetch_effr_data()

    # 检查是否有足够的数据进行分析
    data_available = [treasury_2y_data, treasury_data, market_data, sofr_data, effr_data]
    available_count = sum(1 for data in data_available if data is not None)

    if available_count >= 2:  # 至少需要2个数据点才能进行基本分析
        # 计算 SOFR-EFFR 利差（如果两个数据都可用）
        spread = None
        if sofr_data is not None and effr_data is not None:
            spread = sofr_data['value'] - effr_data['value']

        # 准备显示信息
        treasury_2y_str = f"{treasury_2y_data['description']}: {treasury_2y_data['value']:.2f}%" if treasury_2y_data else "2Y 国债收益率: 无法读取"
        treasury_str = f"{treasury_data['description']}: {treasury_data['value']:.2f}%" if treasury_data else "10Y 国债收益率: 无法读取"
        market_str = f"{market_data['description']}: {market_data['value']:.2f}" if market_data else "VIX 波动率指数: 无法读取"
        sofr_str = f"{sofr_data['description']}: {sofr_data['value']:.4f}%" if sofr_data else "SOFR 隔夜融资利率: 无法读取"
        effr_str = f"{effr_data['description']}: {effr_data['value']:.4f}%" if effr_data else "EFFR 实际联邦基金利率: 无法读取"

        report = f"""
        --- 每日市场监控快报 ---
        数据日期范围: 最近交易日数据 ({available_count}/5 数据可用)
        {treasury_2y_str}
        {treasury_str}
        {market_str}
        {sofr_str}
        {effr_str}
        """

        if spread is not None:
            report += f"利差 (SOFR-EFFR): {spread:.4f}%\n"
        else:
            report += "利差 (SOFR-EFFR): 无法计算 (缺少利率数据)\n"

        report += "------------------------\n"
        print(report)

        # 只有在有足够数据时才进行预警分析
        if spread is not None:
            logging.info(f"SUCCESS: Spread={spread:.4f}%")

            # 预警：利差 > 0.1% 表示融资紧张
            if spread > 0.10:
                warning_msg = "⚠️ ALERT: SOFR-EFFR 利差异常！融资基差升高，流动性可能正在收紧。"
                print(warning_msg)
                logging.warning(warning_msg)
            else:
                print("✅ 融资市场状况正常")

        # 预警：VIX > 20 表示市场波动性升高
        if market_data is not None and market_data['value'] > 20:
            warning_msg = "⚠️ ALERT: 市场波动性升高！需要关注风险。"
            print(warning_msg)
            logging.warning(warning_msg)
if __name__ == "__main__":
    main()
