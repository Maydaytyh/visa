# 澳大利亚签证处理时间爬虫

从澳大利亚移民局官网爬取全球签证处理时间数据。

## 功能特点

- ✅ 爬取所有43种澳大利亚签证类型
- ✅ 自动识别和处理签证子类别（Visa Stream）
- ✅ 获取50%和90%处理时间数据
- ✅ 增量写入 JSON，爬取中途中断不丢失已获取数据
- ✅ 生成JSON数据文件
- ✅ 提供可视化网页界面（含状态信息和排序功能）
- ✅ 支持搜索筛选（300ms 防抖）

## 安装依赖

```bash
pip install selenium beautifulsoup4 webdriver-manager
```

## 使用方法

### 1. 运行爬虫

```bash
# 爬取前5个签证（默认）
python scraper.py

# 爬取前10个签证
python scraper.py 10

# 爬取所有签证
python scraper.py all

# 爬取所有签证并在解析失败时输出调试 HTML 文件
python scraper.py all --debug
```

> **`--debug` 说明**：默认情况下，解析失败时不会生成调试文件。添加 `--debug` 参数后，若某个签证页面解析失败，会自动保存 `debug_visa_<编号>.html` 供排查。

### 2. 查看结果

运行完成后会生成 `visa_data.json` 文件。

在浏览器中打开 `index.html` 查看可视化界面。

## 数据结构

```json
{
  "last_updated": "2026-01-19T00:00:00.000000",
  "source_url": "https://immi.homeaffairs.gov.au/...",
  "visa_count": 50,
  "visas": [
    {
      "visa_type": "Temporary Activity visa (subclass 408)",
      "visa_value": "408",
      "visa_stream": "Entertainment Activities",
      "processing_time_50_percent": "50% processed in 11 Days",
      "processing_time_90_percent": "90% processed in 35 Days",
      "status": "Within standard processing timeframe",
      "submitted_info": "Your application was submitted today .",
      "query_date": "2026-01-19T00:00:00.000000"
    }
  ]
}
```

## 关于子类别（Visa Stream）

某些签证类型包含多个子类别，例如：

- **Temporary Activity visa (408)**: 8个子类别（Entertainment Activities、Sporting Activities等）
- **Business Innovation and Investment (888)**: 3个子类别（Business Innovation、Investor等）
- **Student visa (500)**: 多个子类别（按学历级别）

爬虫会自动检测并爬取所有子类别的数据。

## 关于"N/A"数据

部分签证显示"N/A"是正常现象，原因：

1. 签证已停止接受新申请
2. 处理时间因个案而异，官方未提供统一数据
3. 新推出的签证类型，数据尚未公布

## 数据来源

数据来源：[Australian Department of Home Affairs - Global Visa Processing Times](https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-processing-times/global-visa-processing-times)

## 注意事项

- 处理时间数据仅供参考，实际处理时间可能因个案情况而异
- 建议定期运行爬虫以获取最新数据
- 优化后每个签证等待时间约 2-4 秒（取决于网速），爬取所有签证大约需要 5-8 分钟
