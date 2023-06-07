import socket
import os
import json
import logging
import sys
import threading
import time
import queue
from urllib.parse import parse_qs

from http_parser import HTTPParser

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


# HTML-Antwort basierend auf Bankdaten generieren - für HTTP GET
def generate_html(bank_data: BankData):
    price_all = bank_data.sum_stock_price()
    BANK_ID = int(os.environ.get("BANK_ID"))
    # HTML-Code für die Antwort
    response_html = """
                <!DOCTYPE html>
                <html lang="de">
                  <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Bank</title>
                  </head>
                  <body>
                """
    response_html += f"<h1>Bank {BANK_ID}</h1>"
    response_html += "<h2>Bankdaten</h2>"
    response_html += f"<p> <b>Bank amount:</b> {round(bank_data.get_bank_amount(), 2)} € </p>"
    response_html += f"<p> <b>portfolio value:</b> {round(price_all, 2)} € </p>"
    response_html += f"<p> <b>Total value of bank:</b> {round(price_all + bank_data.get_bank_amount(), 2)}</p>"
    response_html += f"<p> <b>Kredite:</b> {bank_data.credits} </p>"
    response_html += """"""
    response_html += "<h2>Stocks</h2>"

    # Formular für das Abschicken von POST-Requests
    response_html += """
                <form action="" method="POST">
                """
    response_html += f"<p><b>Kredite geben/zurückzahlen:</b> <input type=\"text\" id=\"credits\" name=\"credits\"/></p>"
    response_html += f"<p><b>Einzahlung:</b> <input type=\"text\" id=\"deposit\" name=\"deposit\"/></p>"
    response_html += f"<p><b>Abhebung:</b> <input type=\"text\" id=\"payout\" name=\"payout\"/></p>"
    for stock_name in bank_data.stocks:
        response_html += f"<p><b>{stock_name}</b> --> Preis: {bank_data.stocks[stock_name][1]}€  --> Menge: {bank_data.stocks[stock_name][0]} --> <b>Ver-/kaufen:</b> <input type=\"text\" id=\"{stock_name}\" name=\"{stock_name}\"/></p>"
    response_html += """
                    <button>Send Post Request</button>
                </form>
                """
    return response_html


# HTTP-Socket-Kommunikation mit HTML-Antwort behandeln
# und die entsprechenden Aktionen ausführen
def handle_http_socket(sock: socket, bank_data: BankData):
    request = sock.recv(4096).decode("utf-8")
    # HTTP-Request parsen
    parser = HTTPParser()
    parser.parse(request.split("\r\n"))
    response = "Invalid".encode("utf-8")

    # HTTP-Response generieren für GET-Request
    if parser.method == "GET" and parser.version == "HTTP/1.1" and parser.path == '/':
        logging.info("GET request received")
        response_type = "html"
        response = generate_html(bank_data).encode("utf-8")
        http_response = [
            'HTTP/1.1 200 OK',
            f'Content-Type: {response_type}',
            f'Content-Length: {len(response)}',
            '',
            response.decode()
        ]
        response = "\r\n".join(http_response).encode("utf-8")

    # HTTP-Response generieren für POST-Request
    elif parser.method == "POST" and parser.version == "HTTP/1.1" and parser.path == '/':
        logging.info("POST request received")
        params = parse_qs(parser.body)
        for stock in params:
            if stock == "deposit":
                bank_data.bankAmount += float(params[stock][0])
            elif stock == "payout":
                bank_data.bankAmount -= float(params[stock][0])
            elif stock == "credits":
                add_credits = float(params[stock][0])
                bank_data.credits += add_credits
            else:
                add_amount = float(params[stock][0])
                bank_data.add_stock_amount(stock, add_amount)

        response_type = "html"
        response = "HTTP/1.1 303 See Other\r\n"
        response += "Location: {}\r\n".format(parser.path)
        response += "\r\n"
        response = response.encode('utf-8')

    sock.sendall(response)
    sock.close()


# Bei jeder neuen Client-Verbindung startet diese Funktion einen neuen Thread,
# um die Kommunikation mit dem Client über den angegebenen Socket zu handhaben.
def accept_http_connections(sock: socket, bank_data: BankData):
    while True:
        client_socket, addr = sock.accept()
        threading.Thread(target=handle_http_socket, args=(client_socket, bank_data)).start()

def main():
    setup_logger()

    bankData = BankData()

    # Ausgaben, wenn der Bank-Server gestartet wird
    BANK_ID = int(os.environ.get("BANK_ID"))
    UDP_PORT = 5000 + BANK_ID - 1
    total_price = bankData.sum_stock_price()
    logging.info(f"Bank with ID {BANK_ID} started on port {UDP_PORT} with total portfolio: " + str(total_price) + "€")
    # # bankData.sum_stock_price()

    http_port = os.environ.get('HTTPPORT') if os.environ.get('HTTPPORT') else 8000

    # # Socket für UDP-Kommunikation mit Exchange-Server
    exchange_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    exchange_socket.bind(('0.0.0.0', UDP_PORT))

    # Socket für HTTP-Kommunikation mit Clients
    http_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    http_socket.bind(('0.0.0.0', http_port))
    http_socket.listen(1)

    # Threads für HTTP- und UDP-Kommunikation starten
    http_thread = threading.Thread(target=accept_http_connections, args=(http_socket, bankData))
    http_thread.start()

    data_queue = queue.Queue()
    udp_thread = threading.Thread(target=handle_udp_socket, args=(exchange_socket, data_queue))
    udp_thread.start()

    # Daten für Performance-Messung
    msg_count = 0
    start_time = time.time()

    while True:
        # Daten aus der Queue holen und verarbeiten
        data = data_queue.get()

        # Wenn keine Daten in der Queue sind, wird die Schleife erneut durchlaufen
        if not data:
            continue

        msg = data.decode("utf-8")

        change_stock = msg.split(",")

        bankData.update_stock_price(change_stock[0], change_stock[1])
        price_all = bankData.sum_stock_price()

        msg_count += 1
        elapsed_time = time.time() - start_time
        # logging.info(f"Updated portfolio: " + str(price_all) + "€")

        # Alle 10s Durchsatz und Anzahl der Nachrichten pro Sekunde ausgeben
        if elapsed_time >= 10:
            throughput = msg_count / elapsed_time
            throughput = round(throughput, 2)
            logging.info(f"Throughput: {throughput} msg/s. Msg_count: {msg_count}. portfolio: " + str(price_all) + "€")
            msg_count = 0
            start_time = time.time()


main()

