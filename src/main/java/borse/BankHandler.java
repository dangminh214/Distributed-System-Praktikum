package borse;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;


public class BankHandler {

    private static final int BUFFER_SIZE = 256;
    private static final int TIMEOUT_IN_MS = 1000;

    private final InetAddress address;

    private final int port;

    private final DatagramSocket receiver;

    public BankHandler(InetAddress sensorAddress, int sensorPort, DatagramSocket receiver) {
        address = sensorAddress;
        port = sensorPort;
        this.receiver = receiver;
    }

    public void sendMessage(String msg) throws IOException {
        DatagramPacket request = new DatagramPacket(msg.getBytes(),msg.length(),address,port);
        receiver.send(request);
    }

    public String getMessage() {
        byte[] buffer = new byte[BUFFER_SIZE];
        DatagramPacket response = new DatagramPacket(buffer, BUFFER_SIZE);
        try {
            receiver.setSoTimeout(TIMEOUT_IN_MS);
            receiver.receive(response);
        } catch (Exception e) {
            return "Package from " + address +":"+ port + "could not be received!";
        }
        return new String(response.getData(),0,response.getLength());
    }
}
