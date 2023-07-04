struct LoanRequest {
    1: double amount,
}

enum LoanResponse {
    APPROVED,
    DENIED
}


service BankService {
    LoanResponse requestLoan(1: LoanRequest request)
}