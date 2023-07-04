package borse;

import java.util.Random;

public class RandomDataGenForMsg {

  private static final Random random = new Random();
  

  public RandomDataGenForMsg() {
  }


  public static synchronized int getData(int min, int max) {
    return random.nextInt(max - min + 1) + min;
  }

}
