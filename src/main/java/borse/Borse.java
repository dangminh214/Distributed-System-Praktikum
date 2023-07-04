package borse;


import java.io.*;
import java.util.Timer;
import java.util.TimerTask;
import java.lang.System;

public class Borse  {

    private final BankHandler[] handlers;

    private final Timer mainTimer;
    private final String borseName;
    public Borse(String borseName, BankHandler[] handlers) throws IOException {
        System.out.println(borseName + " starts");
        this.mainTimer = new Timer();
        this.handlers = handlers;
        this.borseName= borseName;
    }

    public void startPullingData(int delay) {
        mainTimer.schedule(new TimerTask() {
            @Override
            public void run() {
                broadcastToBanks();
            }
        }, 0, delay);
    }
    public void broadcastToBanks() {
        try {
            for (BankHandler handler : handlers) {
                if (handler != null) {
                    String msg = new Message().toString();
                    handler.sendMessage(msg);
                }
            }
        } catch (IOException ignored) {}
    }

}
