package bank;

import org.apache.thrift.TException;
import org.apache.thrift.server.TServer;
import org.apache.thrift.server.TSimpleServer;
import org.apache.thrift.transport.TServerSocket;
import org.apache.thrift.transport.TServerTransport;
import org.apache.thrift.transport.TTransportException;
import thrift_container.BankService;
import thrift_container.LoanRequest;
import thrift_container.LoanResponse;

public class RPC_SupportClass extends Thread implements BankService.Iface{
  private TServer server;
  private Bank bank;
  public RPC_SupportClass(Bank bank){
    this.bank= bank;
  }
  @Override
  public void run(){
    startServer();
  }
  public void startServer(){
    String temp = System.getenv("RPCPORT");
    if(temp != null) {
      int rpcPort = Integer.parseInt(temp);
      TServerTransport transport = null;
      try {
        transport = new TServerSocket(rpcPort);
        server = new TSimpleServer(
            new TServer.Args(transport).processor(new BankService.Processor<>(this)));
        server.serve();
      } catch (TTransportException e) {
        e.printStackTrace();
      }

    }
  }
  @Override
  public LoanResponse requestLoan(LoanRequest request) throws TException {
    if(this.bank.getCurrentValue()> request.getAmount()) {
      this.bank.setCurrentValue(this.bank.getCurrentValue()- (int)request.getAmount());
      return LoanResponse.APPROVED;
    }
    return LoanResponse.DENIED;

  }


}
