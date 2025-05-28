document.getElementById('user_type').addEventListener('change', function () {
    var shopkeeperDetails = document.getElementById('shopkeeper-details');
    var buyerDetails = document.getElementById('buyer-details');

    if (this.value == 'shopkeeper') {
        shopkeeperDetails.style.display = 'block';
        buyerDetails.style.display = 'none';
    } else if (this.value == 'buyer') {
        shopkeeperDetails.style.display = 'none';
        buyerDetails.style.display = 'block';
    }
});
