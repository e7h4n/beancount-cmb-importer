'''PDF 导入测试'''

import unittest
from datetime import datetime
from beancount.core.amount import Amount
from beancount.core.number import D
from beancount.core import data
from beancmb.pdf_importer import CmbPdfImporter


class CmbPdfImporterTest(unittest.TestCase):
    '''PDF 导入测试'''

    def setUp(self):
        self.account_name = "Assets:Bank:Checking"
        self.main_file_path = "tests/main.bean"
        self.importer = CmbPdfImporter(self.account_name, self.main_file_path)

    def test_extract(self):
        '''Test extracting transactions from a sample PDF file'''

        with open("tests/法人流水-20200330110203.pdf", "rb") as pdf_file:
            entries = self.importer.extract(pdf_file)

        self.assertEqual(len(entries), 1685)

    def test_specific_transaction(self):
        '''Test extracting transactions from a sample PDF file'''
        with open("tests/法人流水-20200330110203.pdf", "rb") as pdf_file:
            entries = self.importer.extract(pdf_file)

        target_index = 12  # 从 0 开始计数，所以第 12 个条目的索引是 11
        target_date = datetime.strptime("2019-03-29", "%Y-%m-%d").date()
        target_amount = Amount(D("-2.00"), "CNY")
        target_payee = "快捷支付"
        target_narration = "清算资金-借记卡核算专户 待清算电子交换汇差-网联待"

        if len(entries) > target_index and isinstance(entries[target_index], data.Transaction):
            entry = entries[target_index]

            date_matches = entry.date == target_date
            amount_matches = any([posting.units == target_amount for posting in entry.postings])
            payee_matches = entry.payee == target_payee
            narration_matches = entry.narration == target_narration

            self.assertTrue(date_matches, f"Date does not match. Expected: {target_date}, Actual: {entry.date}")
            self.assertTrue(amount_matches, f"Amount does not match. Expected: {target_amount}")
            self.assertTrue(payee_matches, f"Payee does not match. Expected: {target_payee}, Actual: {entry.payee}")
            self.assertTrue(narration_matches, f"Narration does not match. Expected: {target_narration}, Actual: {entry.narration}")
        else:
            self.fail("The target index is out of range or not a Transaction entry.")

    def test_balance_entry(self):
        '''测试 Balance 语句'''

        with open("tests/法人流水-20200330110203.pdf", "rb") as pdf_file:
            entries = self.importer.extract(pdf_file)

        target_date = datetime.strptime("2019-03-31", "%Y-%m-%d").date()
        target_balance = Amount(D("10513.92"), "CNY")

        found_balance = False

        for entry in entries:
            if isinstance(entry, data.Balance) and entry.date == target_date:
                self.assertEqual(entry.amount, target_balance, "Balance amount does not match.")
                found_balance = True
                break

        self.assertTrue(found_balance, "The balance entry for the specific date was not found.")


class CmbPdfImporterTestAfterLastBalance(unittest.TestCase):
    '''测试导入的日期是否晚于最后一条 balance'''

    def setUp(self):
        self.account_name = "Assets:Bank:Checking"
        self.main_file_path = "tests/last-balance-20200328.bean"
        self.importer = CmbPdfImporter(self.account_name, self.main_file_path)

    def test_extract_transactions_after_last_balance(self):
        '''日期应该都晚于最后的 balance'''

        with open("tests/法人流水-20200330110203.pdf", "rb") as pdf_file:
            entries = self.importer.extract(pdf_file)

        last_balance_date = datetime.strptime("2020-03-28", "%Y-%m-%d").date()

        for entry in entries:
            if isinstance(entry, data.Transaction) or isinstance(entry, data.Balance):
                self.assertGreaterEqual(entry.date, last_balance_date, "Transaction or balance date is before the last balance date in main.bean")

    def test_specific_balance_entry(self):
        '''最后应该插入一条 balance'''

        with open("tests/法人流水-20200330110203.pdf", "rb") as pdf_file:
            entries = self.importer.extract(pdf_file)

        target_date = datetime.strptime("2020-03-29", "%Y-%m-%d").date()
        target_balance = Amount(D("103607.49"), "CNY")

        balance_count = 0

        for entry in entries:
            if isinstance(entry, data.Balance) and entry.date == target_date:
                self.assertEqual(entry.amount, target_balance, "Balance amount does not match.")
                balance_count += 1

        self.assertEqual(balance_count, 1, "There should be exactly one balance entry for the specific date.")

    def test_entries_count_on_specific_date(self):
        '''验证导入的交易记录数量'''

        with open("tests/法人流水-20200330110203.pdf", "rb") as pdf_file:
            entries = self.importer.extract(pdf_file)

        target_date = datetime.strptime("2020-03-28", "%Y-%m-%d").date()

        count = 0

        for entry in entries:
            if (isinstance(entry, data.Transaction) or isinstance(entry, data.Balance)) and entry.date == target_date:
                count += 1

        self.assertEqual(count, 8, "There should be exactly 8 entries for the specific date.")


class CmbPdfImporterCustomAccountTest(unittest.TestCase):
    '''PDF 导入测试，验证去向账户的自定义行为'''

    def setUp(self):
        self.account_name = "Assets:Bank:Checking"
        self.outcoming_account_name = "Equity:UnknownAccount"
        self.main_file_path = "tests/main.bean"
        self.importer = CmbPdfImporter(self.account_name, self.main_file_path,
                                       self.outcoming_account_name)

    def test_custom_outcoming_account(self):
        with open("tests/法人流水-20200330110203.pdf", "rb") as file:
            imported_entries = self.importer.extract(file)
            for entry in imported_entries:
                if isinstance(entry, data.Transaction):
                    second_posting = entry.postings[1]
                    self.assertEqual(second_posting.account, self.outcoming_account_name)


if __name__ == '__main__':
    unittest.main()
