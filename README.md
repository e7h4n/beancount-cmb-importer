# Beancount CMB Importer

Beancount CMB Importer 是一个用于将招商银行 PDF 交易流水导入 Beancount 的 Python 库。

## 安装

使用 pip 安装 Beancount CMB Importer：

```bash
pip install beancount-cmb-importer
```

## 注意事项

* 导入的交易，会默认添加一个去向账户 `Equity:UFO`，目前还不支持自定义这个去向账户
* 在导入时，会识别主账本中对应账户的最后一次 balance 记录的日期，只有晚于这个日期的交易才会被导入

## 使用方法

1. 登陆招商银行手机银行 App，把交易流水发送到您的邮箱中。然后下载邮箱中的附件，并把附件解压之后的 pdf 放在 documents 目录下。
2. 在您的 Beancount 文件夹中，创建一个新的 Python 脚本（例如：config.py），并将以下代码复制到脚本中：
```python
from beancmb.pdf_importer import CmbPdfImporter

CONFIG = [
    CmbPdfImporter('Assets:Current:CMB', './main.bean'),
]
```
3. 使用 `bean-extract` 来提取交易记录: `bean-extract config.py documents/`。这将从 PDF 文件中提取交易并将其转换为 Beancount 格式。您可以将其复制并粘贴到您的 Beancount 主文件中。


## License

MIT.
