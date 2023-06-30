from threading import Lock
import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config_bank.json") # Pfad zur Konfigurationsdatei für die Banken 

class Customer:
    name: str
    amount: float

    def __init__(self, name: str, amount: float):
        self.name = name
        self.amount = amount

# Verwaltung der Bankdaten
class BankData:
    bankAmount = 0.0
    bank_name = ""
    lock = Lock()
    requested_money = 0.0
    credits = 0.0
    stocks = {}

    # Initialisieren der Bankdaten
    def __init__(self):
        BANK_ID = int(os.environ.get("BANK_ID"))

        f = open(CONFIG_PATH)
        config = json.load(f)

         # Bankdaten aus der Konfigurationsdatei basierend auf BANK_ID laden
        for b in config["banks"]:
            if b["id"] == BANK_ID:
                self.bankAmount = b["amount_bank"]
                self.bank_name = b["name"]
                self.credits = b["credits"]
                for s in b["stocks"]:
                    self.stocks[s["stock_name"]] = [s["amount"], s["price"]]


   # Berechnen des Gesamtwerts aller Aktien, die eine Bank besitzt
    def sum_stock_price(self):
        self.lock.acquire()
        price_all = 0.0
        for s in self.stocks:
            price_all += self.stocks[s][0] * self.stocks[s][1]
        price_all = round(price_all, 2)
        self.lock.release()
        return price_all

    # Aktualisieren des Preises einer Aktie - für UDP
    def update_stock_price(self, stock, new_price):
        self.lock.acquire()
        change_price = self.stocks[stock]
        change_price[1] = float(new_price)
        self.stocks[stock] = change_price
        self.lock.release()

    # Abrufen des gesamten Bankguthabens
    def get_bank_amount(self):
        return self.bankAmount - self.credits

    def get_requested_money(self):
        return self.requested_money
    
   # Hinzufügen des angegebenen Betrags zur angegebenen Aktie
   # Bankguthaben wird entsprechend aktualisiert 
    def add_stock_amount(self, stock, add_amount):
        self.lock.acquire()
        new_amount = self.stocks[stock][0] + add_amount
        if stock in self.stocks and stock and new_amount >= 0:
            self.bankAmount += (-1 * float(add_amount) * self.stocks[stock][1])
            self.stocks[stock][0] = new_amount
        self.lock.release()

    # Kredite hinzufügen oder abziehen
    def change_credit(self, amount):
        self.lock.acquire()
        self.credits += amount
        self.lock.release()

    def get_credit(self):
        return self.credits

    # Auszahlen des angegebenen Betrags
    def payout(self, amount):
        self.lock.acquire()
        self.bankAmount -= amount
        self.lock.release()

    # Einzahlen des angegebenen Betrags
    def deposit(self, amount):
        self.lock.acquire()
        self.bankAmount += amount
        self.lock.release()

    def add_bankamount(self, amount):
        self.lock.acquire()
        self.bankAmount += amount
        self.lock.release()

    def reduce_bankamount(self, amount):
        self.lock.acquire()
        self.bankAmount -= amount
        self.lock.release()
