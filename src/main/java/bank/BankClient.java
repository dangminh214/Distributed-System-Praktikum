package bank;
import borse.Code;
import borse.Message;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;

public class BankClient extends Thread {
  public static final String REQUEST_CANNOT_BE_PROCESSED = "500 Request cannot be processed.";
  public static final String BAD_REQUEST = "400 Request is missing Content-Length or Content-Type is not text/plain";
  public static final String DEFAULT_ANSWER = "200 OK";
  public static final String DENY_ANSWER = "402 NOT ALLOW";

  public static final int CONTENT_LENGTH_BEGIN_INDEX = 16;
  private static final int CONTENT_TYPE_BEGIN_INDEX = 14;
  private final Socket connection;
  private final BufferedReader reader;
  private final OutputStream writer;
  private int contentLength;
  private String contentType;
  private String statusMessage;


  private final BufferedReader in;
  private final OutputStream out;
  private boolean checkRequest ;

  private Bank bank;
  public BankClient(Socket clientConnection, Bank bank)
      throws IOException {
    this.bank= bank;
    connection = clientConnection;
    reader = new BufferedReader(new InputStreamReader(clientConnection.getInputStream()));
    writer = clientConnection.getOutputStream();
    in = new BufferedReader(new InputStreamReader(clientConnection.getInputStream()));
    out = clientConnection.getOutputStream();
    this.checkRequest = false;
  }
  @Override
  public synchronized void run() {
    try {
      String bodyContent;
      while (!connection.isClosed()) {
        parseHeader();
        bodyContent = getBody();
        if (bodyContent == null|| bodyContent.equals(""))
          break;
        else{
          String transactionType= "";
          int money = 0;
          Code code = null;
          int quantity =0;
          String[] parameters = bodyContent.split("&");
          for (String parameter : parameters) {
            String[] keyValue = parameter.split("=");
            if(keyValue[0].equals("transactionType")&& keyValue.length==2){
              transactionType = keyValue[1];
            }
            else if(keyValue[0].equals("money") && keyValue.length==2 ){
              money = getMoney(keyValue[1]);
            }
            else if(keyValue[0].equals("code") && keyValue.length==2){
              code = getCode(keyValue[1]);
            }
            else if(keyValue[0].equals("quantity")  && keyValue.length==2 ){
              quantity = getQuantity(keyValue[1]);
            }
          }
          evaluateRequest(transactionType,money, code,quantity);
        }
      }
    } catch (IOException ignored) {}
  }

  private void evaluateRequest(String transactionType, int money, Code code, int quantity)
      throws IOException {
    if(transactionType.equals("")) return;
    else if(transactionType.equals("sendMoney") ){
      bank.setCurrentValue(bank.getCurrentValue()+money);
      this.statusMessage= DEFAULT_ANSWER;
      sendAnswer("Send money: "+money);
    }
    else if(transactionType.equals("lendMoney")){
      if(bank.getCurrentValue() < money){
        this.statusMessage= DENY_ANSWER;
        bank.setCurrentValue(bank.getCurrentValue()-money);
        sendAnswer("Exceed amount of money");
      }
      else {
        this.statusMessage= DEFAULT_ANSWER;
        bank.setCurrentValue(bank.getCurrentValue()-money);
        sendAnswer("Lend money "+money);
      }
    }
    else if(transactionType.equals("buyStock")){
      Message message = bank.getSavedMessage().get(code);
      if(message == null){
        this.statusMessage= DENY_ANSWER;
        sendAnswer("Stock Code does not exist");
      }
      else{
        if(message.getQuantity()< quantity){
          this.statusMessage= DENY_ANSWER;
          sendAnswer("This Code doesnt have enough");
        }
        else{
          message.setQuantity(message.getQuantity()-quantity);
          this.statusMessage= DEFAULT_ANSWER;
          sendAnswer("Transaction successful");
        }
      }
    }
  }

  private void parseHeader() throws IOException {
    statusMessage = DEFAULT_ANSWER;
    contentLength = -1;
    contentType = "NOT OKAY";
    String data;
    if (!requestLineIsValid(reader.readLine())) {
      contentLength = 0;
      statusMessage = REQUEST_CANNOT_BE_PROCESSED;
      return;
    }
    if(this.checkRequest) {
      setCheckRequest(false);
      return;
    }
    data = reader.readLine();
    while (data != null && !data.equals("")) {
      if (data.startsWith("Content-Length: ")) {
        contentLength = getContentLength(data);
      }
      else if (data.startsWith("Content-Type: ")) {
        contentType = getContentType(data);

      }
      data = reader.readLine();
    }
    if (requestMissesProperHeaderFields()) {
      contentLength = 0;
      statusMessage = BAD_REQUEST;
      sendAnswer("");
    }
  }
  private int getMoney(String data){
    try {
      return Integer.parseInt(data);
    } catch (Exception ignored) {}
    return 0;
  }
  private Code getCode(String data){
    try {
      return Code.valueOf(data);
    } catch (Exception ignored) {}
    return null;
  }
  private int getQuantity(String data){
    try {
      return Integer.parseInt(data);
    } catch (Exception ignored) {}
    return 0;
  }
  private String getBody() throws IOException {
    if (contentLength == 0)
      return null;
    StringBuilder data = new StringBuilder();
    while(contentLength > 0) {
      int i = reader.read();
      data.append((char)i);
      --contentLength;
    }
    return data.toString();
  }
  private void sendAnswer(String msg) throws IOException {
    String http = "HTTP/1.1 " + statusMessage + "\r\n"
        + "Bank: bank1\r\n"
        + "Content-Type: text/plain\r\n"
        + "Content-Length: "+ msg.length() +" \r\n\r\n"
        +msg;
    System.out.println(http);
    writer.write(http.getBytes());
  }
  private String getContentType(String data) {
    try {
      return data.substring(CONTENT_TYPE_BEGIN_INDEX);
    } catch (Exception ignored) {}
    return "NOT OKAY";
  }
  private int getContentLength(String data) {
    try {
      return Integer.parseInt(data.substring(CONTENT_LENGTH_BEGIN_INDEX));
    } catch (Exception ignored) {}
    return -1;
  }
  private boolean requestLineIsValid(String data) throws IOException {

    if (data == null)
      return false;
    String[] tokens = data.split(" ");
    if (tokens.length != 3)
      return false;
    if(tokens[0].equals("GET")&& tokens[1].equals("/getData?") && tokens[2].equals("HTTP/1.1")){
      statusMessage = DEFAULT_ANSWER;
      String http = "HTTP/1.1 " + statusMessage + "\r\n"
          + "Server: bank9000\r\n"
          + "Content-Type: text/plain\r\n"
          + "Content-Length: "+ String.valueOf(bank.getCurrentValue()).length()+ " \r\n\r\n"
          + bank.getCurrentValue();
      out.write(http.getBytes());
      System.out.println(http);
      out.flush();
      this.checkRequest= true;
      return true;
    }
    return tokens[0].equals("POST") && tokens[1].equals("/") && tokens[2].equals("HTTP/1.1");
  }
  private boolean requestMissesProperHeaderFields() {
    return contentLength == -1 || !contentType.equals("application/x-www-form-urlencoded");
  }
  public void setCheckRequest(boolean checkRequest) {
    this.checkRequest = checkRequest;
  }


}
