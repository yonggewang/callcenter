from typing import List, Optional
from pydantic import BaseModel

class Option(BaseModel):
    name: str # e.g. "Spicy Level"
    choices: List[str] # ["Mild", "Medium", "Spicy"]

class MenuItem(BaseModel):
    id: str
    name: str
    price: float
    description: str
    options: List[Option] = []

class Restaurant(BaseModel):
    id: str
    name: str
    phone_number: str # The Twilio number assigned
    menu: List[MenuItem]

# Mock Database
restaurants_db = [
    Restaurant(
        id="rest_1",
        name="Wok & Roll",
        phone_number="+15550001",
        menu=[
            MenuItem(
                id="item_1", 
                name="Kung Pao Chicken", 
                price=12.50, 
                description="Spicy chicken with peanuts",
                options=[Option(name="Spice Level", choices=["Mild", "Medium", "Spicy"])]
            ),
            MenuItem(
                id="item_2", 
                name="Spring Rolls", 
                price=5.00, 
                description="Vegetable rolls",
                options=[]
            )
        ]
    ),
    Restaurant(
        id="rest_lanzhou",
        name="Lanzhou Hand Pulled Noodles",
        phone_number="+15550002", # Assign a unique Twilio number for this restaurant
        menu=[
            MenuItem(
                id="lz_1",
                name="Signature Beef Hand-Pulled Noodles",
                price=14.95,
                description="Clear beef broth with radish, cilantro, and tender beef slices",
                options=[Option(name="Noodle Width", choices=["Thin", "Standard", "Wide", "Flat"])]
            ),
            MenuItem(
                id="lz_2",
                name="Braised Beef Noodles",
                price=15.95,
                description="Rich, dark soy-based broth with chunks of slow-cooked beef",
                options=[Option(name="Spice Level", choices=["Non-spicy", "Mild", "Medium", "Hot"])]
            ),
            MenuItem(
                id="lz_3",
                name="Spicy Cumin Lamb Skewers",
                price=12.00,
                description="5 pieces of grilled lamb seasoned with authentic cumin and chili",
                options=[]
            ),
            MenuItem(
                id="lz_4",
                name="Dry Stirred Beef Noodles",
                price=14.50,
                description="No-soup noodles topped with minced beef and special sauce",
                options=[Option(name="Noodle Width", choices=["Thin", "Standard", "Wide"])]
            ),
            MenuItem(
                id="lz_5",
                name="Cold Sesame Noodles",
                price=11.50,
                description="Refreshing cold noodles with peanut sesame sauce and cucumber",
                options=[]
            ),
            MenuItem(
                id="lz_6",
                name="Scallion Pancake",
                price=6.50,
                description="Crispy, flaky savory pancake with fresh scallions",
                options=[]
            ),
            MenuItem(
                id="lz_7",
                name="Smashed Cucumber Salad",
                price=7.50,
                description="Garlic-heavy refreshing cucumber salad with vinegar and chili oil",
                options=[]
            ),
            MenuItem(
                id="lz_8",
                name="Lanzhou Fried Rice",
                price=13.50,
                description="Wok-fired rice with egg, peas, and choice of protein",
                options=[Option(name="Add Protein", choices=["None", "Beef", "Chicken", "Shrimp"])]
            ),
            MenuItem(
                id="lz_9",
                name="Stewed Beef Tripe",
                price=9.50,
                description="Tender beef tripe marinated in spiced soy sauce",
                options=[]
            ),
            MenuItem(
                id="lz_10",
                name="Malt Rice Tea",
                price=3.50,
                description="Traditional sweet and warm malt beverage",
                options=[]
            ),
            MenuItem(
                id="lz_11",
                name="Spicy Beef Baozi",
                price=8.95,
                description="3 pieces of steamed buns filled with spicy minced beef",
                options=[]
            ),
            MenuItem(
                id="lz_12",
                name="Vegetable Hand-Pulled Noodles",
                price=13.50,
                description="Fresh noodles in vegetable broth with seasonal greens and tofu",
                options=[Option(name="Broth", choices=["Clear", "Mushroom"])]
            )
        ]
    )
]

def get_restaurant_by_phone(phone: str) -> Optional[Restaurant]:
    """
    Finds a restaurant based on the Twilio phone number receiving the call.
    Note: Twilio sends phone numbers in E.164 format (e.g., +1234567890).
    """
    for restaurant in restaurants_db:
        if restaurant.phone_number == phone:
            return restaurant
    return None
