import logging
import sys
import os
import random
import socket
import time

UDP_PORT = 5000
IP = "bank"

stocks = {
    "Coca-Cola": 50.00,
    "META": 500.00,
    "Apple": 2000.00,
    "Alibaba": 150.0,
    "Alphabet": 250.00,
    "Tesla": 700.00,
}


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
def main():
    setup_logger()

    logging.info("UDP target port: %s" % UDP_PORT)

    number_of_banks = int(os.environ.get("num_Banks"))

    msg_count = 0
    start_time = time.time()

    # ask environment
    while True:
        # time.sleep(1)

        # Simuliert das Senden von Aktienkursdaten an verschiedene Banken, indem zufällige eine Aktie ausgewählt wird und
        # dafür ein zufälliger Preis und ein zufälliges Volumen generiert und
        # in einer Nachricht an alle Banken gesendet werden.
        stock = random.choice(list(stocks.keys()))

        # Der Preis liegt aufgrund der Volatilität des Aktienmarktes zwischen
        # 95% und 105% des ursprünglichen Preises.
        price = round(random.uniform(0.95, 1.05) * stocks[stock], 2)
        volume = random.randint(1, 100)

        message = f"{stock},{price},{volume}"

        try:
            # Senden der Nachricht an alle Banken mittels UDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            for i in range(0, number_of_banks):
                # udp-socket sendet an alle Banken die Nachricht
                sock.sendto(message.encode('utf-8'), (IP + str(i + 1), UDP_PORT + i))

            # logging.info(f"Sent: {message}")
            msg_count += 1
            elapsed_time = time.time() - start_time

            # Durchsatz berechnen - für Performance-Tests
            if elapsed_time >= 5:
                throughput = msg_count / elapsed_time
                throughput = round(throughput, 2)
                logging.info(f"Throughput: {throughput} msg/s. Messages sent: {msg_count}")
                msg_count = 0
                start_time = time.time()
        except:
            logging.info("Error sending message")
            exit(-1)


if __name__ == "__main__":
    main()



