package thrift_container;

/**
 * Autogenerated by Thrift Compiler (0.17.0)
 *
 * DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
 *  @generated
 */

@javax.annotation.Generated(value = "Autogenerated by Thrift Compiler (0.17.0)", date = "2023-05-30")
public enum LoanResponse implements org.apache.thrift.TEnum {
  APPROVED(0),
  DENIED(1);

  private final int value;

  private LoanResponse(int value) {
    this.value = value;
  }

  /**
   * Get the integer value of this enum value, as defined in the Thrift IDL.
   */
  @Override
  public int getValue() {
    return value;
  }

  /**
   * Find a the enum type by its integer value, as defined in the Thrift IDL.
   * @return null if the value is not found.
   */
  @org.apache.thrift.annotation.Nullable
  public static LoanResponse findByValue(int value) { 
    switch (value) {
      case 0:
        return APPROVED;
      case 1:
        return DENIED;
      default:
        return null;
    }
  }
}
