from typing import List, Optional, Dict
from pydantic import BaseModel
import logging
import re
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptionChoice(BaseModel):
    id: str
    name: str
    price_extra: float = 0.0

class Option(BaseModel):
    name: str 
    choices: List[OptionChoice]

class MenuItem(BaseModel):
    id: str 
    name: str
    price: float
    category: str 
    options: List[Option] = []

class Restaurant(BaseModel):
    id: str
    name: str
    phone_number: str
    menu: List[MenuItem]
    categories: List[str]

# --- FALLBACK EMBEDDED MENU ---
EMBEDDED_MENU_DATA = [
    {"id": "10", "name": "Pork Dumplings (8pcs)", "price": 10.99, "cat": "APPETIZERS", "opt": "Options: 1: Steamed, 2: Pan-fried"},
    {"id": "11", "name": "Steamed Stuffed Buns (5pcs)", "price": 11.99, "cat": "APPETIZERS", "opt": ""},
    {"id": "12", "name": "Sesame Balls (6pcs)", "price": 6.99, "cat": "APPETIZERS", "opt": ""},
    {"id": "13", "name": "Coconut Balls (6pcs)", "price": 6.99, "cat": "APPETIZERS", "opt": ""},
    {"id": "14", "name": "Smashed Cucumbers", "price": 7.99, "cat": "APPETIZERS", "opt": ""},
    {"id": "15", "name": "Rice Cake w. Brown Sugar", "price": 7.99, "cat": "APPETIZERS", "opt": ""},
    {"id": "16", "name": "Five Spiced Braised Beef", "price": 15.99, "cat": "APPETIZERS", "opt": ""},
    {"id": "17", "name": "Pumpkin Cake (6pcs)", "price": 6.99, "cat": "APPETIZERS", "opt": ""},
    {"id": "18", "name": "Mala Braised Beef", "price": 15.99, "cat": "APPETIZERS", "opt": ""},
    {"id": "19", "name": "Spring Rolls (2pcs)", "price": 4.50, "cat": "APPETIZERS", "opt": ""},
    {"id": "20", "name": "ShanXi Shaved Noodles", "price": 14.99, "cat": "NOODLE SOUP", "opt": "Variety: 1, 2, 3, 4, 5"},
    {"id": "21", "name": "ShanXi Chili Oil Noodles", "price": 14.99, "cat": "NOODLE SOUP", "opt": "Variety: 1, 2, 3, 4, 5 (+$6)"},
    {"id": "22", "name": "Vegetarian LaMian", "price": 11.99, "cat": "NOODLE SOUP", "opt": ""},
    {"id": "23", "name": "Tomato Egg Noodle Soup", "price": 12.99, "cat": "NOODLE SOUP", "opt": ""},
    {"id": "24", "name": "Seafood Noodles", "price": 18.99, "cat": "NOODLE SOUP", "opt": ""},
    {"id": "25", "name": "Beijing ZhaJiang Mian", "price": 14.99, "cat": "NOODLE SOUP", "opt": ""},
    {"id": "26", "name": "Cold Noodles", "price": 14.99, "cat": "NOODLE SOUP", "opt": "Variety: 1, 2, 3, 4 (+$6)"},
    {"id": "27", "name": "Pickled Cabbage Beef Noodle", "price": 14.99, "cat": "NOODLE SOUP", "opt": "Variety: 1, 2, 3, 4, 5"},
    {"id": "28", "name": "Clear Broth Beef Noodle", "price": 14.99, "cat": "NOODLE SOUP", "opt": "Variety: 1, 2, 3, 4, 5"},
    {"id": "29", "name": "Spicy Beef Noodle Soup", "price": 14.99, "cat": "NOODLE SOUP", "opt": "Variety: 1, 2, 3, 4, 5"},
    {"id": "30", "name": "Braised Beef Noodle Soup", "price": 14.99, "cat": "NOODLE SOUP", "opt": "Variety: 1, 2, 3, 4, 5"},
    {"id": "40", "name": "ShanXi Stir-Fried Shaved Noodles", "price": 14.99, "cat": "FRIED RICE & CHAO MIAN", "opt": "Variety: 1, 2, 3, 4"},
    {"id": "41", "name": "House Special Fried Rice", "price": 14.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "42", "name": "Beef Fried Rice", "price": 13.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "43", "name": "Chicken Fried Rice", "price": 12.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "44", "name": "Pork Fried Rice", "price": 12.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "45", "name": "Shrimp Fried Rice", "price": 13.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "46", "name": "Egg Fried Rice", "price": 10.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "47", "name": "House Special ChaoMian", "price": 15.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "48", "name": "Beef ChaoMian", "price": 14.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "49", "name": "Chicken ChaoMian", "price": 14.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "50", "name": "Shrimp ChaoMian", "price": 14.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "51", "name": "Pork ChaoMian", "price": 14.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "52", "name": "Vegetable ChaoMian", "price": 12.99, "cat": "FRIED RICE & CHAO MIAN", "opt": ""},
    {"id": "60", "name": "Beef w. Spicy Broth", "price": 18.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "61", "name": "Fish Fillet w. Spicy Broth", "price": 18.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "62", "name": "Spicy Wok Fish Fillet", "price": 21.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "63", "name": "Spicy Wok Beef", "price": 21.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "64", "name": "Spicy Wok Shrimp", "price": 21.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "65", "name": "Fish Fillet w. Pickled Cabbage", "price": 21.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "66", "name": "Eggplant Tofu in Pot", "price": 18.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "67", "name": "Shredded Pork w. Garlic Sauce", "price": 17.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "68", "name": "Fried Diced Chicken (ChongQing Style)", "price": 18.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "69", "name": "Mongolian Beef", "price": 15.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "70", "name": "General Tso's Chicken", "price": 15.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "71", "name": "Kung Pao Chicken", "price": 17.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "72", "name": "MaPo Tofu", "price": 14.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "73", "name": "Eggplant w. Garlic Sauce", "price": 14.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "74", "name": "Stir-Fried Green Beans", "price": 13.99, "cat": "SAUTEED DISHES", "opt": ""},
    {"id": "80", "name": "Classic Boba Milk Tea", "price": 5.95, "cat": "DRINKS", "opt": ""},
    {"id": "81", "name": "Brown Sugar Boba Milk Tea", "price": 5.95, "cat": "DRINKS", "opt": ""},
    {"id": "82", "name": "Thai Boba Milk Tea", "price": 5.95, "cat": "DRINKS", "opt": ""},
    {"id": "83", "name": "Matcha Boba Milk Tea", "price": 5.95, "cat": "DRINKS", "opt": ""},
    {"id": "84", "name": "Mango Iced Green Tea", "price": 5.95, "cat": "DRINKS", "opt": ""},
    {"id": "85", "name": "Chinese Herbal Tea (Can)", "price": 3.50, "cat": "DRINKS", "opt": ""},
    {"id": "86", "name": "Rock Sugar and Pear (Can)", "price": 3.50, "cat": "DRINKS", "opt": ""},
    {"id": "87", "name": "Coconut Milk", "price": 3.99, "cat": "DRINKS", "opt": ""},
    {"id": "88", "name": "Soda", "price": 2.25, "cat": "DRINKS", "opt": "Options: 1: Coke, 2: Sprite, 3: Fanta, 4: Diet Coke"}
]

def build_menu_from_embedded() -> List[MenuItem]:
    menu_items = []
    noodle_types = [OptionChoice(id="1", name="Thin"), OptionChoice(id="2", name="Wide"), OptionChoice(id="3", name="Thick"), OptionChoice(id="4", name="Leek Leaf"), OptionChoice(id="5", name="Rice Noodles")]
    varieties_meat = [OptionChoice(id="1", name="Beef"), OptionChoice(id="2", name="Pork"), OptionChoice(id="3", name="Chicken"), OptionChoice(id="4", name="Shrimp"), OptionChoice(id="5", name="Fried Tofu")]

    for data in EMBEDDED_MENU_DATA:
        item_id = data["id"]
        item_options = []
        
        # Noodle logic
        if 20 <= int(item_id) <= 39:
            item_options.append(Option(name="Noodle Type", choices=noodle_types))

        # Variety/Selection logic
        opt_text = data["opt"].lower()
        if "variety" in opt_text:
            extra = 6.0 if "+$6" in opt_text else 0.0
            ids = re.findall(r"\d", data["opt"].split("(")[0])
            choices = [OptionChoice(id=cid, name=next((v.name for v in varieties_meat if v.id == cid), "Other"), price_extra=extra if extra > 0 else 0.0) for cid in ids]
            item_options.append(Option(name="Variety", choices=choices))
        elif "options" in opt_text:
            matches = re.findall(r"(\d):\s*([^,]+)", data["opt"])
            choices = [OptionChoice(id=m[0], name=m[1].strip()) for m in matches]
            item_options.append(Option(name="Selection", choices=choices))

        menu_items.append(MenuItem(
            id=item_id,
            name=data["name"],
            price=data["price"],
            category=data["cat"],
            options=item_options
        ))
    return menu_items

# --- INITIALIZATION ---
# Always use embedded menu to ensure it WORKS immediately
full_menu = build_menu_from_embedded()
logger.info(f"Initialized with {len(full_menu)} embedded items.")

restaurants_db = [
    Restaurant(
        id="rest_1",
        name="Lanzhou Hand Pulled Noodles", 
        phone_number="+19809832989",
        menu=full_menu,
        categories=list(set([i.category for i in full_menu]))
    )
]

def get_restaurant_by_phone(phone: str) -> Optional[Restaurant]:
    return restaurants_db[0]

def find_item_by_id(input_text: str, restaurant: Restaurant) -> Optional[MenuItem]:
    digits = "".join(re.findall(r"\d", input_text))
    if not digits:
        word_map = {"ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18", "nineteen": "19", "twenty": "20"}
        for word, val in word_map.items():
            if word in input_text.lower():
                digits = val
                break

    if digits and len(digits) >= 2:
        target_id = digits[:2]
        logger.info(f"[find_item_by_id] Search ID: '{target_id}' (In menu of {len(restaurant.menu)} items)")
        for item in restaurant.menu:
            if str(item.id).strip() == target_id:
                logger.info(f"[find_item_by_id] MATCH: {item.name}")
                return item
    
    return None

def find_item_by_speech(speech_text: str, restaurant: Restaurant) -> Optional[MenuItem]:
    item = find_item_by_id(speech_text, restaurant)
    if item: return item
    
    cleaned = speech_text.lower().replace(".", "").strip()
    for item in restaurant.menu:
        if item.name.lower() in cleaned or cleaned in item.name.lower():
            return item
    return None
