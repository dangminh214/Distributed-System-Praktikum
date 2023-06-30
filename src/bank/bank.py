import socket
import os
import logging
import string
import sys
import threading
import time
import queue
from urllib.parse import parse_qs
from gen.bank import RPCBankService
from http_parser import HTTPParser
from bankData import BankData

from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.transport import TSocket, TTransport

from bank_rpc import BankRPCHandler, BankRPCRequest

CONFIG_PATH = os.path.join(os.path.dirname(__file__),
                           "config_bank.json")  # Pfad zur Konfigurationsdatei für die Banken


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
    response_html += f"<p> <b>Bank amount:</b> {round(bank_data.get_bank_amount())} € </p>"
    response_html += f"<p> <b>portfolio value:</b> {round(price_all, 2)} € </p>"
    response_html += f"<p> <b>Total value of bank:</b> {round(price_all + bank_data.get_bank_amount(), 2)} € </p>"
    response_html += f"<p> <b>geliehenes Geld:</b> {round(bank_data.get_requested_money(), 2)} € </p>"
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
    response_html += "<h2>Geldtransfer an andere Bank</h2>"
    response_html += f"<p><b>Menge:</b> <input type=\"text\" id=\"transfer\" name=\"transfer\"/>"
    response_html += f" <b>Ziel:</b> <input type=\"text\" id=\"target\" name=\"target\"/></p>"
    response_html += """
                    <button>Send Post Request</button>
                </form>
                """
    return response_html


# HTTP-Socket-Kommunikation mit HTML-Antwort behandeln
# und die entsprechenden Aktionen ausführen
def handle_http_socket(sock: socket, bank_data: BankData, rpc_port: int):
    request = sock.recv(4096).decode("utf-8")
    # HTTP-Request parsen
    parser = HTTPParser()
    parser.parse(request.split("\r\n"))
    response = "Invalid".encode("utf-8")

    banks = os.environ.get('BANKS').split(",")
    rpc_request = BankRPCRequest(banks, rpc_port)

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
        if "deposit" in params:
            deposit = float(params["deposit"][0])
            bank_data.deposit(deposit)
        elif "payout" in params:
            if bank_data.bankAmount - float(params["payout"][0]) >= 0:
                payout = float(params["payout"][0])
                bank_data.payout(payout)
            else:
                logging.info("Not enough money in bank")
                payout = float(params["payout"][0])
                amount = payout - bank_data.bankAmount
                logging.info(f"Requesting {amount} from other banks")
                start_time_rpc = time.time()
                success = rpc_request.request_money(amount)
                elapsed_time = time.time() - start_time_rpc
                logging.info(f"RPC-Request took {round(elapsed_time, 4)} seconds")
                if success:
                    bank_data.requested_money += amount
                    bank_data.add_bankamount(amount)
                    bank_data.payout(float(params["payout"][0]))
                else:
                    logging.info("Bankanfrage wurde abgelehnt!")
        elif "credits" in params:
            add_credits = float(params["credits"][0])
            bank_data.change_credit(add_credits)
        elif "transfer" in params and "target" in params:
            if bank_data.bankAmount - float(params["transfer"][0]) >= 0:
                transfer_amount = float(params["transfer"][0])
                target = str(params["target"][0])
                start_time_rpc = time.time()
                success = rpc_request.transfer_money(target, transfer_amount)
                elapsed_time = time.time() - start_time_rpc
                elapsed_time = round(elapsed_time, 4)
                logging.info(f"RPC-Request took {elapsed_time} seconds")
                if success:
                    bank_data.reduce_bankamount(transfer_amount)
            else:
                logging.info("Not enough money in bank")
        else:
            for stock in params:
                if stock != "deposit" and stock != "payout" and stock != "credits" and stock != "transfer" and stock != "target":
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
def accept_http_connections(sock: socket, bank_data: BankData, rpc_port: int):
    while True:
        client_socket, addr = sock.accept()
        threading.Thread(target=handle_http_socket, args=(client_socket, bank_data, rpc_port)).start()


def init_rpc_server(data: BankData, port):
    handler = BankRPCHandler(data)
    processor = RPCBankService.Processor(handler)
    transport = TSocket.TServerSocket(host='0.0.0.0', port=port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)

    logging.info('Statring the RPC server on port ' + str(port) + '...')
    server.serve()
    logging.info('done.')


def main():
    setup_logger()

    bankData = BankData()

    # Ausgaben, wenn der Bank-Server gestartet wird
    BANK_ID = int(os.environ.get("BANK_ID"))
    UDP_PORT = 5000 + BANK_ID - 1
    total_price = bankData.sum_stock_price()
    logging.info(f"Bank with ID {BANK_ID} started on port {UDP_PORT} with total portfolio: " + str(total_price) + "€")

    http_port = os.environ.get('HTTPPORT') if os.environ.get('HTTPPORT') else 8000
    rpc_port = os.environ.get('RPCPORT') if os.environ.get('RPCPORT') else 9090

    banks = os.environ.get('BANKS').split(",")

    # Socket für UDP-Kommunikation mit Exchange-Server
    exchange_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    exchange_socket.bind(('0.0.0.0', UDP_PORT))

    # Socket für HTTP-Kommunikation mit Clients
    http_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    http_socket.bind(('0.0.0.0', http_port))
    http_socket.listen(1)

    # Threads für HTTP- und UDP-Kommunikation starten
    http_thread = threading.Thread(target=accept_http_connections, args=(http_socket, bankData, rpc_port))
    http_thread.start()

    udp_data_queue = queue.Queue()
    udp_thread = threading.Thread(target=handle_udp_socket, args=(exchange_socket, udp_data_queue))
    udp_thread.start()

    rpc_thread = threading.Thread(target=init_rpc_server, args=(bankData, rpc_port))
    rpc_thread.start()

    # Daten für Performance-Messung
    msg_count = 0
    start_time = time.time()

    while True:
        # Daten aus der Queue holen und verarbeiten
        data = udp_data_queue.get()

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
        if elapsed_time >= 5:
            throughput = msg_count / elapsed_time
            throughput = round(throughput, 2)
            logging.info(f"Throughput: {throughput} msg/s. Msg_count: {msg_count}. portfolio: " + str(price_all) + "€")
            msg_count = 0
            start_time = time.time()


main()

