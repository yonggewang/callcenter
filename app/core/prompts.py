class Prompts:
    GREETING = (
        "Welcome to Lanzhou Hand Pulled Noodles. "
        "Please enter or say the two-digit ID for the dish you would like to order."
    )
    
    # ID based prompts
    SPECIFY_ID = "Please enter the two-digit code for your dish, for example, 1 0 or 2 5."
    
    # Variety prompts
    VARIETY_PROMPT_TEMPLATE = "For {dish_name}, we have multiple options: {options_list}. Please say the number or press the key for your choice."
    
    # Confirmation prompts
    CONFIRM_DISH_TEMPLATE = "You selected {dish_name}. Is that correct? Say 1 for yes or 2 for no."
    
    # Error prompts
    ID_NOT_FOUND = "I'm sorry, I couldn't find a dish with that ID. Please try again with the two-digit code."
    INVALID_SELECTION = "I'm sorry, that selection is not valid. Please choose from the available options."
    
    # Flow prompts
    ADD_MORE = "I've added {dish_name} to your order. Would you like to order anything else? Say 1 or yes to continue, or 2 or no if you are finished."
    
    SUMMARY_TEMPLATE = (
        "Your order includes: {order_summary}. "
        "The total amount is ${total_price:.2f}. "
        "Would you like to place this order? Say 1 for yes or 2 for no."
    )
    
    FINAL_SUCCESS = "Great! Your order has been placed. It will be ready for pickup soon. Thank you for calling Lanzhou Hand Pulled Noodles!"
    FINAL_CANCEL = "No problem. Your order has been cancelled. Have a nice day!"
    
    ERROR_SILENCE = "I didn't hear anything. Please enter the two-digit ID for your dish."
    ERROR_NOT_UNDERSTOOD = "I'm sorry, I didn't quite catch that. Please use the keypad or say the numbers clearly."
    
    FALLBACK_GOODBYE = "I haven't heard from you in a while, so I will hang up now. Goodbye."
