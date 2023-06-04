import socket
import os
import json
import logging
import sys
import threading
import time
import queue

CONFIG_PATH = os.path.join(os.path.dirname(__file__),
                           "config_bank.json")  # Pfad zur Konfigurationsdatei für die Banken


# Verwaltung der Bankdaten
class BankData:
    bankAmount = 0.0
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
                self.credits = b["credits"]
                for s in b["stocks"]:
                    self.stocks[s["stock_name"]] = [s["amount"], s["price"]]

    # Berechnen des Gesamtwerts aller Aktien, die eine Bank besitzt
    def sum_stock_price(self):
        price_all = 0.0
        for s in self.stocks:
            price_all += self.stocks[s][0] * self.stocks[s][1]
        price_all = round(price_all, 2)
        return price_all

    # Aktualisieren des Preises einer Aktie - für UDP
    def update_stock_price(self, stock, new_price):
        change_price = self.stocks[stock]
        change_price[1] = float(new_price)
        self.stocks[stock] = change_price

    # Abrufen des gesamten Bankguthabens
    def get_bank_amount(self):
        return self.bankAmount - self.credits

    # Hinzufügen des angegebenen Betrags zur angegebenen Aktie
    # Bankguthaben wird entsprechend aktualisiert
    def add_stock_amount(self, stock, add_amount):
        new_amount = self.stocks[stock][0] + add_amount
        if stock in self.stocks and stock and new_amount >= 0:
            self.bankAmount += (-1 * float(add_amount) * self.stocks[stock][1])
            self.stocks[stock][0] = new_amount


# Logger für die Ausgabe von Informationen und Fehlern einrichten
def setup_logger():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


# UDP-Socket-Kommunikation behandeln
def handle_udp_socket(sock: socket, bank_queue: queue.Queue):
    while True:
        data, addr = sock.recvfrom(1024)
        bank_queue.put(data)  # Daten in die Warteschlange einfügen


def main():
    setup_logger()

    bankData = BankData()

    # Ausgaben, wenn der Bank-Server gestartet wird
    BANK_ID = int(os.environ.get("BANK_ID"))
    UDP_PORT = 5000 + BANK_ID - 1
    bankData.sum_stock_price()

    # # Socket für UDP-Kommunikation mit Exchange-Server
    exchange_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    exchange_socket.bind(('0.0.0.0', UDP_PORT))

    data_queue = queue.Queue()
    udp_thread = threading.Thread(target=handle_udp_socket, args=(exchange_socket, data_queue))
    udp_thread.start()

    # Daten für Performance-Messung
    msg_count = 0
    start_time = time.time()

    while True:
        # Daten aus der Queue holen und verarbeiten
        data = data_queue.get()

        msg = data.decode("utf-8")

        change_stock = msg.split(",")

        bankData.update_stock_price(change_stock[0], change_stock[1])
        price_all = bankData.sum_stock_price()

        msg_count += 1
        elapsed_time = time.time() - start_time

        # Alle 10s Durchsatz und Anzahl der Nachrichten pro Sekunde ausgeben
        if elapsed_time >= 10:
            throughput = msg_count / elapsed_time
            throughput = round(throughput, 2)
            logging.info(f"Throughput: {throughput} msg/s. Msg_count: {msg_count}. portfolio: " + str(price_all) + "€")
            msg_count = 0
            start_time = time.time()


main()

