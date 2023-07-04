package borse;
public class Message {
  private Code code;
  private int quantity ;
  private int price;


  public Code getCode() {
    return code;
  }

  public void setCode(Code code) {
    this.code = code;
  }

  public int getQuantity() {
    return quantity;
  }

  public void setQuantity(int quantity) {
    this.quantity = quantity;
  }

  public int getPrice() {
    return price;
  }

  public void setPrice(int price) {
    this.price = price;
  }
  public Message(){
    this.price = RandomDataGenForMsg.getData(100,300);
    this.code = Code.values()[ RandomDataGenForMsg.getData(0, Code.values().length-1)];
    this.quantity = RandomDataGenForMsg.getData(-10,50);
  }
  public Message(Code code, int quantity, int price){
    this.code = code;
    this.price = price;
    this.quantity = quantity;
  }
    public String toString(){
    return quantity+"," + code.toString()+ ","+ price;
  }


}
