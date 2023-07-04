package bank;

import borse.Code;
import borse.Message;
import connection.Establisher;
import java.io.IOException;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.UnknownHostException;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import org.apache.thrift.protocol.TBinaryProtocol;
import org.apache.thrift.protocol.TProtocol;
import org.apache.thrift.transport.TSocket;
import org.apache.thrift.transport.TTransport;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import thrift_container.BankService.Client;
import thrift_container.LoanRequest;
import thrift_container.LoanResponse;
import udp.UDPHandler;
import udp.UDPMessage;

public class Bank extends Thread implements Establisher {
    private static final String PREPARE_TOPIC = "prepare";
    private static final String COMMIT_TOPIC = "commit";
    private static final String FINISH_TOPIC = "finish";

    private final UDPHandler handler;
    private final String bankName;
    private int currentValue;
    private int HTTP_DEFAULT_PORT;
    private int port;
    private Map<String, Long> startTimes; // Add this line
    private BankClient bankClient;
    private final ServerSocket serverSocket;
    private HashMap<Code, Message> savedMessage;
    private boolean running;
    private HashMap<String, Integer> rpcAdress;
    private boolean bankrupt;
    private RPC_SupportClass rpc;
    private int amount;
    private MqttClient client;
    private int respones;
    private int bankSize;
    private boolean check;

    public Bank(String name, int port, int httpPort) throws IOException {
        this.startTimes = new HashMap<>();
        this.HTTP_DEFAULT_PORT = httpPort;
        this.bankName = name;
        this.currentValue = 0;
        savedMessage = new HashMap<>();
        this.port = port;
        this.running = true;
        serverSocket = new ServerSocket(HTTP_DEFAULT_PORT);
        this.bankrupt = false;
        rpc = new RPC_SupportClass(this);
        amount=0;
        respones=0;
        check=true;
        bankSize=3;
        String bankRPCs = System.getenv("RPCBANKS");
        if (bankRPCs != null) {
            rpcAdress= new HashMap<>();
            String[] bankEndpoints = bankRPCs.split(",");
            for (String endpoint : bankEndpoints) {
                String[] parts = endpoint.split(":");
                String bankName = parts[0];
                int portName = Integer.parseInt(parts[1]);
                rpcAdress.put(bankName,portName);
            }
        }
        try{
            connectMQTT();
        }
        catch (MqttException e) {
            System.out.println("MQTT Exception");
            throw new RuntimeException(e);
        }
        this.handler = new UDPHandler(this) {
            @Override
            public UDPMessage getMessage() {
                String message = bankName + ": RTT check";
                return new UDPMessage(message);
            }
        };
    }
    private void connectMQTT() throws MqttException {
        client = createClient("broker",1883);
        client.subscribe(PREPARE_TOPIC);
        client.subscribe(COMMIT_TOPIC);
        client.subscribe(FINISH_TOPIC);

        client.setCallback(new MqttCallback() {
            @Override
            public void connectionLost(Throwable throwable) {
                System.out.println("Connection loss");
            }

            @Override
            public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
                System.out.println("TOPIC:"+ topic);
                if (topic.equals(PREPARE_TOPIC)) {
                    handlePrepareMessage(mqttMessage);
                } else if (topic.equals(COMMIT_TOPIC)) {
                    handleCommitMessage(mqttMessage);
                }
                else if (topic.equals(FINISH_TOPIC)) {
                    handleFinishMessage(mqttMessage);
                }
            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken iMqttDeliveryToken) {


            }
        });
    }
        private void handleFinishMessage(MqttMessage mqttMessage) {
            String name =  new String(mqttMessage.getPayload());            
            if(!name.equals(bankName)){
                this.setCurrentValue(this.getCurrentValue()-this.amount);
                System.out.println("Current value: "+ this.getCurrentValue());
            long startTime = startTimes.getOrDefault(name, 0L);

            long endTime = System.nanoTime();
            long rescueTime = endTime - startTime;
            
            System.out.println("Time to rescue Bank: " + (rescueTime ) + " s");
            }
          
            }

    private void handlePrepareMessage(MqttMessage mqttMessage) {
        String split[] = new String(mqttMessage.getPayload()).split(";");
        String name = split[0];
        String money = split[1];
        if(!name.equals(bankName)){
            startTimes.put(name, System.nanoTime());
            this.amount= Integer.parseInt(money)/2;
            sendMQTTMessage(COMMIT_TOPIC, name +";"+(amount< this.getCurrentValue()?"true":"false"));
        }
    }

    private void handleCommitMessage(MqttMessage mqttMessage) {
        String split[] = new String(mqttMessage.getPayload()).split(";");
        String name = split[0];
        String vote = split[1];
        if(name.equals(bankName)){
            respones++;
            System.out.println(respones);
            if(vote.equals("false")) check = false;
            if(respones== bankSize-1&& check){
                sendMQTTMessage(FINISH_TOPIC, name);
                respones=0;
            }
        }
    }


    public MqttClient createClient(String host,int port){
        MqttClient publisher = null;
        String id = UUID.randomUUID().toString();
        while (publisher== null){
            try {
                String ip =InetAddress.getByName(host).toString().substring(host.length()+1);
                publisher= new MqttClient("tcp://"+ip+":"+port,id);

            } catch (UnknownHostException e) {
                throw new RuntimeException(e);
            } catch (MqttException e) {
                throw new RuntimeException(e);
            }
        }
        while(!publisher.isConnected()){
            try {
                publisher.connect();
            } catch (MqttException e) {
                throw new RuntimeException(e);
            }
        }
        return publisher;

    }


    public boolean isBankrupt() {
        return bankrupt;
    }

    public void setBankrupt(boolean bankrupt) {
        this.bankrupt = bankrupt;
    }
    @Override
    public void run() {
        handler.start();
        rpc.start();
       
        try {
            while (running) {
                if(this.getCurrentValue()<0){
                        System.out.println("------------------------------BANKRUPT!!!!!!!!!!-------------------------");
                        String amount = String.valueOf(this.getCurrentValue());
                        sendMQTTMessage(PREPARE_TOPIC,this.bankName+";"+amount);
                }
                Socket client = serverSocket.accept();
                this.bankClient = new BankClient(client, this);
                this.bankClient.start();
            }
            System.out.println("Bank stops working");
        } catch (Exception ignored) {
        }
    }
    private void sendMQTTMessage(String topic, String mess){
        System.out.println("Send mqtt from Bank with message "+ mess +" with topic "+ topic );
        try {
            MqttMessage msg = new MqttMessage();
            msg.setPayload(mess.getBytes());
            msg.setQos(2);
            msg.setRetained(true);
            client.publish(topic,msg);

        } catch (MqttException ignore) {
            ignore.printStackTrace();
        }
    }

    private void askForHelp() {
        boolean allDenied = true;
        System.out.println("SENDING HELPING REQUEST");
        for (Map.Entry<String, Integer> entry : rpcAdress.entrySet()) {
            String hostRpc = entry.getKey();
            int portRpc = entry.getValue();
            try{
                TTransport transport;
                transport = establishConnection(hostRpc, portRpc);
                TProtocol protocol = new TBinaryProtocol(transport);
                Client client = new Client(protocol);
                Double value = Double.valueOf(-this.getCurrentValue());
                long startTime = System.nanoTime();
                LoanRequest request = new LoanRequest(value);
                LoanResponse response = client.requestLoan(request);
                long endTime = System.nanoTime();
                long rtt = endTime - startTime;
                System.out.println("RTT: " + rtt + " nanoseconds");
                System.out.println("Response: "+ response);
                if(response.equals(LoanResponse.APPROVED)){
                    System.out.println(hostRpc+ " success to rescue");
                    this.setCurrentValue(0);
                    allDenied = false;
                    break;
                }
                else if(response.equals(LoanResponse.DENIED)){
                    System.out.println(hostRpc+" fail to rescue");
                }
                else {
                    System.out.println("Else case: "+ response);
                }
            }
            catch (Exception e){
                e.printStackTrace();
            }
        }
        if(allDenied){
            setBankrupt(true);
        }
    }

    public HashMap<Code, Message> getSavedMessage() {
        return savedMessage;
    }

    public int getPort() {
        return this.port;
    }

    public void addSavedMessage(Code code, int quantity, int price) {
        Message msg = savedMessage.get(code);
        if (msg == null) {
            msg = new Message(code, quantity, price);
            savedMessage.put(code, msg);
        } else {
            int newQuantity = msg.getQuantity() + quantity;
            int newPrice = price;
            msg.setQuantity(newQuantity);
            msg.setPrice(newPrice);
            savedMessage.replace(code, msg);
        }
    }

    public int getCurrentValue() {
        return currentValue;
    }

    public void setCurrentValue(int value) {
        this.currentValue = value;
    }
    @Override
    public TSocket establishConnection(String host, int port) {
        TSocket socket = null;
        while (socket == null) {
            try {
                socket = new TSocket(host, port);
            } catch (Exception ignored) {
            }
        }
        while (!socket.getSocket().isConnected())
            try {
                socket.open();
            } catch (Exception e) {
                System.err.println("Error opening socket");
            }
        return socket;
    }
}
