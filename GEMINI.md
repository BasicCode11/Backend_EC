 I've fixed the checkout process. Here's how cart_item and order_item work now:

  CartItem vs. OrderItem

   * `CartItem`: A temporary item in the user's shopping cart.
   * `OrderItem`: A permanent record of a purchased item on an order, with details frozen at the time of sale for
     accurate history.

  The Checkout Process

  When a user checks out, the system now correctly:

   1. Validates stock for each CartItem.
   2. Creates an Order.
   3. Converts CartItems to permanent OrderItems.
   4. Reduces stock_quantity from the correct Inventory records.
   5. Clears the cart.

  Fixes Implemented

  I resolved critical bugs preventing checkout, including incorrect stock checking and reduction, and an order creation
  crash. The system is now consistent and functional.