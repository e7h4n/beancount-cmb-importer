'''招商银行每日信用卡邮件账单导入'''

import base64
import re
from email import parser
from os import path
from datetime import timedelta, datetime, date
from beancount.core import data
from beancount.core.amount import Amount
from beancount.core.number import D
from beancount.ingest import importer
from bs4 import BeautifulSoup
from dateutil.parser import parse as dateparse
from beancmb.util import get_last_balance_date


class CmbDailyEmailImporter(importer.ImporterProtocol):
    """An importer for CMB .eml files."""

    def __init__(self, account, beancount_file):
        self.account_name: str = account
        self.currency = "CNY"
        self.beancount_file = beancount_file

    def identify(self, file):
        return (
            re.match(r"cmb-daily-", path.basename(file.name)) and
            re.search(r"eml", path.basename(file.name))
        )

    def file_name(self, file):
        return 'eml'

    def file_account(self, file):
        return self.account_name

    def file_date(self, file):
        with open(file.name, 'rb') as f:
            eml = parser.BytesParser().parse(fp=f)
            b = base64.b64decode(eml.get_payload()[0].get_payload())
            d = BeautifulSoup(b, "lxml")

            balance_date = d.select(
                '#fixBand3 font[style="font-size:19px;line-height:120%;"]'
            )[0].text.strip().split(" ")[0]

            return dateparse(balance_date).date()

    def extract(self, file, existing_entries=None):
        entries = []
        index = 0

        last_balance_date = get_last_balance_date(self.beancount_file, self.account_name)

        with open(file.name, 'rb') as f:
            eml = parser.BytesParser().parse(fp=f)
            b = base64.b64decode(eml.get_payload()[0].get_payload())
            d = BeautifulSoup(b, "lxml")
            fonts = d.select(
                '#fixBand1 > table > tbody > tr:nth-child(6) font')
            balance = D(240000) - D(fonts[0].text.strip()
                                    [1:].replace('￥', '').replace(',', ''))

            balanceDate = d.select(
                '#fixBand3 font[style="font-size:19px;line-height:120%;"]'
            )[0].text.strip().split(" ")[0]

            transaction_date = dateparse(balanceDate).date()
            balance_date = transaction_date + timedelta(days=1)
            txn_balance = data.Balance(
                account=self.account_name,
                amount=-Amount(balance, 'CNY'),
                meta=data.new_metadata(".", 1000),
                tolerance=None,
                diff_amount=None,
                date=balance_date
            )

            entries.append(txn_balance)

            bands = d.select('#fixBand4')
            for band in bands:
                fonts = band.select(
                    'table tbody tr td table tbody tr td table tbody tr td table tbody tr td font')
                currency = fonts[1].text.strip().split(" ")[0]
                amount = D(fonts[1].text.strip().split(
                    " ")[1].replace(",", ""))
                merchant = fonts[2].text.strip()
                flag = "!"

                amount = Amount(amount, currency)
                meta = data.new_metadata(file.name, index)
                txn = data.Transaction(
                    meta, transaction_date, flag, merchant, None,
                    data.EMPTY_SET,
                    data.EMPTY_SET, [
                        data.Posting(self.account_name, -amount,
                                     None, None, None, None),
                        data.Posting("Equity:UFO", None, None, None, None, None),
                    ])

                entries.append(txn)

        return entries
