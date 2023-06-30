import logging
import random

from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket, TTransport

from bankData import BankData
from gen.bank import RPCBankService

class BankRPCHandler:
    data: BankData

    def __init__(self, data: BankData):
        self.data = data

    def money_transfer(self, target, amount):
        # Ausgabe in der Konsole
        logging.info("RPC - Transferred " + str(amount) + " to " + target)
        self.data.add_bankamount(amount)
        return True
    
    def request(self, amount):
        logging.info("RPC - Requesting Money " + str(amount))
        if self.data.bankAmount - amount >= 0:
            random_boolean = random.choice([True, False])
            if random_boolean:
                self.data.reduce_bankamount(amount)
                return True
            else: 
                return False
        else:
            return False
    
class BankRPCRequest:
    ips = []
    port: int

    def __init__(self, ips, port):
        self.ips = ips
        self.port = port
    
    def transfer_money(self, target, amount):
        logging.info("RPC - Transferring " + str(amount) + " to " + target)
        transport = TSocket.TSocket(target, self.port)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = RPCBankService.Client(protocol)
        transport.open()
        success = client.money_transfer(target, amount)
        transport.close()
        return success
    
    def getRandomBank(self):
        size = len(self.ips)
        index = random.randint(0, (size - 1))
        return self.ips[index]

    def request_money(self, amount):
        for ip in self.ips:
            bank = str(ip)
            bank = bank.replace(" ", "")
            logging.info("RPC - Requesting " + str(amount) + " from " + bank)
            transport = TSocket.TSocket(bank, self.port)
            transport = TTransport.TBufferedTransport(transport)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = RPCBankService.Client(protocol)
            transport.open()
            success = client.request(amount)
            transport.close()
            if success:
                logging.info("Bank wurde gerettet von " + bank)
                return True
        return False
        