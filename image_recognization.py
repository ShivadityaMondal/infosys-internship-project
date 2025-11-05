# image_recognization.py

from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torch
import numpy as np

# ------------------- CLIP Zero-Shot Setup -------------------
# Using a powerful CLIP model for flexible, zero-shot classification
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# EXPANDED CANDIDATE LIST: Now includes all requested items with only two chairs
CANDIDATES =[
    # ------------------ Home Appliances ------------------
    "Television", "Refrigerator", "Ceiling Fan", "Electric Iron for clothes", "Washing Machine",
    "Mixer Grinder Appliance",
    "Split Air Conditioner unit",
    "Microwave Oven", "Water Purifier", "Air Cooler",
    "Vacuum Cleaner", "Induction Stove", "Chimney", "Electric Kettle", "Room Heater",
    "Coffee Maker", "Toaster", "Dishwasher", "Geyser", "Rice Cooker",

    # ------------------ Personal Electronics ------------------
    "Apple iPhone", "Samsung Phone", "Smartphone", "Feature Phone", "Tablet",
    "Laptop", "Desktop Computer", "Monitor", "Keyboard", "Mouse",
    "Smart Watch", "Fitness Band", "Digital Watch", "Earbuds", "Headphones",
    "Bluetooth Speaker", "Power Bank", "Camera", "Tripod", "Printer",

    # ------------------ Clothing & Footwear ------------------
    "Formal Shirt", "Formal Pant", "T-Shirt", "Casual Shirt", "Jeans",
    "Jacket", "Kurta", "Saree", "Dress Garment", "Shorts",
    "Pair of Shoes", "Sandals", "Slippers", "Belt", "Wallet",
    "Sunglasses", "Cap", "Handbag", "Backpack", "Watch Strap",

    # ------------------ Jewelry & Accessories ------------------
    "Wrist Watch (Digital Display)", "Wrist Watch (Analog Display)",
    "Wrist Bracelet", "Necklace Chain", "Pair of Earrings",
    "Reading Spectacles (Glasses)", "Eyeglasses (Power Glasses)",

    # ------------------ Cosmetics & Beauty ------------------
    "Face Cream Jar", "Moisturizer Bottle", "Foundation Makeup", "Face Powder Container",
    "Lipstick Tube", "Lip Gloss", "Nail Polish Bottle",
    "Eye Liner Pen", "Mascara Tube", "Eyeshadow Palette",
    "Shaving Foam Can", "After Shave Lotion", 
    "Sunscreen Lotion Bottle",

    # ------------------ Kitchen & Dining ------------------
    "Bottle", "Mug", "Lunch Box", "Cooker", "Non Stick Pan",
    "Dinner Set", "Cutlery Set", "Water Bottle (Plastic)", "Water Bottle (Steel)", "Mixer Jar", "Frying Pan",
    "Glass Set", "Storage Container", "Knife Set", "Rolling Pin", "Gas Stove",
    "Stainless Steel Utensil Set", "Kitchen Utensil Spatula",

    # ------------------ Furniture & Home Items (Simplified Chairs) ------------------
    "Table", "Desk", "Sofa", "Bed",
    "Plastic Chair", # <-- KEPT
    "Revolving Office Chair", # <-- KEPT (Represents 'rotate chair')
    "Mattress", "Pillow", "Bedsheet", "Curtains", "Wall Clock (Wall Mounted)", 
    "Lamp", "Bookshelf", "Shoe Rack", "Wardrobe", "Study Table",
    "Doormat", "Bath Towel", "Hand Kerchief", "Bathroom Mug", "Plastic Bucket",

    # ------------------ Stationery & Office ------------------
    "Notebook", "Pen", "Pencil", "Eraser", "Calculator",
    "Diary", "File Folder", "Stapler", "Scissors", "Glue Stick",

    # ------------------ Personal Care & Hygiene ------------------
    "Hair Dryer", "Trimmer", "Shaver", "Hair Straightener", "Perfume",
    "Toothbrush (Manual)", "Electric Toothbrush", "Razor", "Comb", "Mirror",
    "Shampoo Bottle", "Body Wash Bottle", "Hair Brush",
    "Adult Diapers", "Sanitary Pad",

    # ------------------ Pharmaceuticals/OTC Medicine ------------------
    "Medicine Blister Pack", "Bottle of Tablets (Medicine)", "Pain Relief Balm (e.g., Zandu Balm)",
    
    # ------------------ Miscellaneous & Outdoor ------------------
    "Umbrella", "Torch", "Travel Bag", "Helmet", "Bicycle",
    "Cricket Bat", "Football", "Yoga Mat", "Water Bottle Holder", "Raincoat",
    "Toy Car", "Small Toy Bike", "Stuffed Toy (Soft Toy)"
]


# ------------------- Unified Recognition -------------------
def recognize_image(image: Image.Image):
    """
    Performs image recognition using the CLIP model against the expanded CANDIDATES list.
    Returns the best matching label and its confidence score (0-100).
    """
    # Ensure image is in RGB format for consistency
    if image.mode != "RGB":
        image = image.convert("RGB")
        
    # Process the image and text labels
    inputs = clip_processor(
        text=CANDIDATES, 
        images=image, 
        return_tensors="pt", 
        padding=True
    )
    
    with torch.no_grad():
        outputs = clip_model(**inputs)
        
    # Get the similarity scores (logits) and apply softmax to get probabilities
    logits = outputs.logits_per_image.softmax(dim=1)[0]
    
    # Get the index of the highest score
    idx = torch.argmax(logits).item()
    
    # Get the label and convert the score to a percentage
    label = CANDIDATES[idx]
    score = float(logits[idx]) * 100
    
    return label, score