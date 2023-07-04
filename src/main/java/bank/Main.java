package bank;

import java.io.IOException;


public class Main {
    public static void main(String[] args) throws IOException {
        Bank bank = new Bank( args[0],Integer.parseInt(args[1]),Integer.parseInt(args[2]));
        bank.start();

    }
}
