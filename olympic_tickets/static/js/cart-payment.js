document.getElementById("open-payment-modal")?.addEventListener("click", () => {
    document.getElementById("payment-modal").style.display = "flex";
});
document.getElementById("cancel-pay")?.addEventListener("click", () => {
    document.getElementById("payment-modal").style.display = "none";
});
document.getElementById("confirm-pay")?.addEventListener("click", () => {
    document.getElementById("real-checkout-form").submit();
});
