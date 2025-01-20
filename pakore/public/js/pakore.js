frappe.ready(function() {
    console.log('Pay button hiddenxx');
    frappe.call({
        method: "pakore.pakore.custom.customer_balance.get_customer_balance",
        callback: function(r) {
            if (r.message) {
                var balanceDiv = document.createElement('div');
                balanceDiv.classList.add('alert-warning');
                balanceDiv.innerHTML = 'Total Unpaid (€): ' + r.message;
                var pageContentWrapper = document.querySelector('.page-content-wrapper');
                if (pageContentWrapper) {
                    pageContentWrapper.insertBefore(balanceDiv, pageContentWrapper.firstChild);
                }
            }
        }
    });
});