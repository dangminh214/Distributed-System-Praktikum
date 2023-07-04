package udp;

public class UDPMessage {
    private final byte[] payload;
    private final int length;

    public UDPMessage(String s) {
        int length = s.length();
        this.length = length;
        this.payload = s.getBytes();
    }
    public byte[] getPayload() {
        return this.payload;
    }

    public int length() {
        return this.length;
    }

    @Override
    public String toString() {
        return new String(this.payload);
    }
}
