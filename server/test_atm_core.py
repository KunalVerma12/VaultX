import os, sys
import json
import unittest
from atm_core import ATM, sha256
print("ATM module imported from:", ATM.__module__)
print("ATM class defined in:", os.path.abspath(sys.modules[ATM.__module__].__file__))
print("ATM.change_pin function:", ATM.change_pin)


TEST_FILE = "test_users.json"

class TestATMCore(unittest.TestCase):
    def setUp(self):
        # make sure to start with a clean file for each test
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)
        self.atm = ATM(data_file=TEST_FILE)

    def tearDown(self):
        # clean up test file
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)

    def test_account_creation(self):
        ok, msg = self.atm.create_account("testuser", "pass123", "1111")
        self.assertTrue(ok)
        self.assertIn("created", msg)
        self.assertIn("testuser", self.atm.users)

    def test_duplicate_account(self):
        self.atm.create_account("testuser", "pass123", "1111")
        ok, msg = self.atm.create_account("testuser", "otherpass", "2222")
        self.assertFalse(ok)
        self.assertIn("exists", msg)

    def test_login_success_and_failure(self):
        self.atm.create_account("alice", "mypassword", "2222")
        ok, msg = self.atm.login("alice", "mypassword")
        self.assertTrue(ok)
        self.assertIn("Logged in", msg)
        ok, msg = self.atm.login("alice", "wrongpass")
        self.assertFalse(ok)
        self.assertIn("Incorrect", msg)

    def test_deposit_and_balance(self):
        self.atm.create_account("bob", "pass", "3333")
        self.atm.login("bob", "pass")
        ok, msg = self.atm.deposit(2000)
        self.assertTrue(ok)
        self.assertAlmostEqual(self.atm.get_balance(), 2000)

    def test_withdraw_correct_pin(self):
        self.atm.create_account("sam", "pass", "4444")
        self.atm.login("sam", "pass")
        self.atm.deposit(1000)
        ok, msg = self.atm.withdraw(200, "4444")
        self.assertTrue(ok)
        self.assertAlmostEqual(self.atm.get_balance(), 800)

    def test_withdraw_incorrect_pin(self):
        self.atm.create_account("sam", "pass", "4444")
        self.atm.login("sam", "pass")
        self.atm.deposit(1000)
        ok, msg = self.atm.withdraw(200, "1234")
        self.assertFalse(ok)
        self.assertIn("Incorrect", msg)

    def test_transfer(self):
        self.atm.create_account("john", "pw", "1234")
        self.atm.create_account("mary", "pw", "1234")
        self.atm.login("john", "pw")
        self.atm.deposit(500)
        ok, msg = self.atm.transfer("mary", 100, "1234")
        self.assertTrue(ok)
        self.assertAlmostEqual(self.atm.get_balance("john"), 400)
        self.assertAlmostEqual(self.atm.get_balance("mary"), 100)

    def test_change_pin(self):
        self.atm.create_account("ella", "p", "0000")
        self.atm.login("ella", "p")
        ok, msg = self.atm.change_pin("0000", "9999")
        self.assertTrue(ok)
        ok, msg = self.atm.withdraw(10, "0000")
        self.assertFalse(ok)
        ok, msg = self.atm.withdraw(10, "9999")
        self.assertTrue(ok)



    def test_rating(self):
        self.atm.create_account("star", "pass", "7777")
        self.atm.login("star", "pass")
        ok, msg = self.atm.submit_rating(5)
        self.assertTrue(ok)
        self.assertEqual(self.atm.users["star"]["rating"], 5)

    def test_json_persistence(self):
        # create account, deposit, then reload and check data persists
        self.atm.create_account("persist", "pw", "1111")
        self.atm.login("persist", "pw")
        self.atm.deposit(123)
        balance_before = self.atm.get_balance()
        self.atm._save()

        # reload into new ATM instance
        new_atm = ATM(data_file=TEST_FILE)
        self.assertIn("persist", new_atm.users)
        self.assertAlmostEqual(new_atm.get_balance("persist"), balance_before)

if __name__ == "__main__":
    unittest.main()
