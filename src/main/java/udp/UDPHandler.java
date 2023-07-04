package udp;

import bank.Bank;
import borse.Code;
import borse.Message;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.SocketTimeoutException;
import java.util.HashMap;

public abstract class UDPHandler extends Thread {

    public static final int BUFFER_SIZE = 512;

    private final DatagramSocket receiver;

    private boolean running;

    private Bank bank;
    private int sentPackets;
    private int lostPackets;
    public UDPHandler(Bank bank) throws SocketException {
        this.bank= bank;
        this.receiver = new DatagramSocket(bank.getPort());
        this.running = true;
        this.sentPackets = 0;
        this.lostPackets = 0;
    }

    public void stopHandler() {
        this.running = false;
    }

    protected abstract UDPMessage getMessage();

    @Override
    public void run() {
        byte[] buffer;
        DatagramPacket request;
        while (running) {
            buffer = new byte[BUFFER_SIZE];
            request = new DatagramPacket(buffer,BUFFER_SIZE);
            if(bank.isBankrupt()) break;
            try {
                receiver.receive(request);
                receiver.send(evaluateData(request.getData(), request.getLength(), request.getAddress(), request.getPort()));
                if(sentPackets!=0){
                    double packetLossRate = (double) lostPackets / sentPackets * 100;
                    System.out.println("Packet loss rate: " + packetLossRate + "%");
                }
            }
            catch (SocketTimeoutException e) {
                System.out.println("UDP packet not arrived: " + e.getMessage());
                lostPackets++;
            }catch (Exception ignored) {
                System.out.println("not be able to catch message ");
                lostPackets++;
            }
            sentPackets++;
        }
        receiver.close();
    }

    private DatagramPacket evaluateData(byte[] packetBytes, int length, InetAddress address, int port) {
        String decodedRequest = new String(packetBytes,0,length);
        String[] requestArray = decodedRequest.split(",");
        int quantity = Integer.parseInt(requestArray[0]);
        String kurzel = requestArray[1];
        int price = Integer.parseInt(requestArray[2]);
        this.bank.addSavedMessage(Code.valueOf(kurzel),quantity,price);
        int oldValue = this.bank.getCurrentValue();
        int newValue = calculate(this.bank.getSavedMessage());
        this.bank.setCurrentValue(newValue);
        int difference = newValue - oldValue;
        if(difference >0 ){
            System.out.println("The Bank receives "+ difference+"$ more than last time");
        }
        else{
            System.out.println("The Bank loses "+ (-difference)+"$ than last time");
        }
        System.out.println("Banks current value: "+ this.bank.getCurrentValue());
        return reply(address, port);
    }
    private int calculate(HashMap<Code, Message> data){
        int sum = this.bank.getCurrentValue();
        for (Message value : data.values()) {
            sum += value.getQuantity() * value.getPrice();
        }
        return sum;
    }
    public DatagramPacket error(InetAddress address, int port) {
        return new DatagramPacket("error".getBytes(), "error".length(), address, port);
    }

    public DatagramPacket reply(InetAddress address, int port) {
        UDPMessage message = getMessage();
        return new DatagramPacket(message.getPayload(), message.length(), address, port);
    }
}


