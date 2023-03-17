'''招行 PDF 导入'''

from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import re
import os
from beancount.core.data import Balance, Transaction, new_metadata, Posting, EMPTY_SET
from beancount.core.amount import Amount
from beancount.core.number import D
from beancount.ingest import importer
from beancount.loader import load_file
import pdfplumber


def get_last_balance_date(main_file_path, account_name):
    '''获取文档中对应账户最后一次对账的时间'''

    entries, _, _ = load_file(main_file_path)
    last_balance_date = None

    for entry in reversed(entries):
        if isinstance(entry, Balance) and entry.account == account_name:
            last_balance_date = entry.date
            break

    return last_balance_date


def is_valid_filename(filename: str) -> bool:
    '''判断文件名是否有效'''

    pattern = re.compile(r'^招商银行交易流水.*\.pdf$')
    return bool(pattern.match(filename))


def process_text_list(text_list):
    '''从文本列表中尝试解析交易记录'''

    result = []
    i = 0
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')

    while i < len(text_list) and text_list[i] != "Date":
        i += 1

    while i < len(text_list):
        if date_pattern.match(text_list[i]):
            date = text_list[i]

            currency = text_list[i + 1]
            if currency == "人民币":
                currency = "CNY"

            amount = float(text_list[i + 2].replace(',', ''))
            balance = float(text_list[i + 3].replace(',', ''))
            channel = text_list[i + 4]

            merchant_parts = []
            i += 5

            while i < len(text_list):
                no_date_match = not date_pattern.match(text_list[i])
                not_verification = "交易流水验真" not in text_list[i]

                if no_date_match and not_verification:
                    merchant_parts.append(text_list[i])
                    i += 1
                else:
                    break

            merchant = " ".join(merchant_parts)

            transaction_dict = {
                "date": date,
                "currency": currency,
                "amount": amount,
                "balance": balance,
                "channel": channel,
                "merchant": merchant,
            }
            result.append(transaction_dict)
        else:
            i += 1

    return result


def extract_transactions(pdf_file: str):
    '''从 pdf 文件中解析交易记录'''

    rows = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            words = [x['text'] for x in page.extract_words()]
            rows += process_text_list(words)

    return rows


class CmbPdfImporter(importer.ImporterProtocol):
    '''招行 pdf 交易流水导入'''

    def __init__(self, account_name, main_file_path, outcoming_account_name="Equity:UFO"):
        self.account_name = account_name
        self.main_file_path = main_file_path
        self.outcoming_account_name = outcoming_account_name

    def identify(self, file):
        return is_valid_filename(os.path.basename(file.name))

    def extract(self, file, existing_entries=None):
        # 解析 PDF，提取交易数据并生成 Beancount 实体
        entries = []
        transactions = extract_transactions(file.name)
        current_date = None
        prev_balance = None

        # 获取 main.bean 中最后一个余额的日期
        last_balance_date = get_last_balance_date(self.main_file_path, self.account_name)

        transaction = None
        for transaction in transactions:
            meta = new_metadata(file.name, 0)
            date = datetime.strptime(transaction['date'], '%Y-%m-%d').date()

            # 跳过 main.bean 中已经存在的交易
            if last_balance_date is not None and date < last_balance_date:
                continue

            payee = transaction['channel']
            narration = transaction['merchant']

            if current_date != date:
                current_date = date
                if prev_balance is not None:
                    rounded_balance = D(prev_balance).quantize(Decimal('.01'),
                                                               rounding=ROUND_HALF_UP)
                    balance_entry = Balance(
                        meta,
                        date,
                        self.account_name,
                        Amount(rounded_balance, transaction['currency']),
                        None,
                        None
                    )
                    entries.append(balance_entry)

            prev_balance = transaction['balance']
            amount = transaction['amount']
            account2 = self.outcoming_account_name

            rounded_amount = D(amount).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

            postings = [
                Posting(self.account_name, Amount(rounded_amount, transaction['currency']),
                        None, None, None, None),
                Posting(account2, None, None, None, None, None)
            ]

            txn = Transaction(meta, date, "!", payee, narration, EMPTY_SET,
                              EMPTY_SET, postings)
            entries.append(txn)

        if prev_balance is not None and transaction is not None:
            rounded_balance = D(prev_balance).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
            balance_entry = Balance(
                meta,
                date + timedelta(days=1),
                self.account_name,
                Amount(rounded_balance, transaction['currency']),
                None,
                None
            )
            entries.append(balance_entry)

        return entries
