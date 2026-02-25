from shared.config import get_settings

settings = get_settings()

# Model configurations
CLASSIFICATION_MODEL = "efficientnet_b4"
CLASSIFICATION_WEIGHTS = "IMAGENET1K_V1"
CLASSIFICATION_INPUT_SIZE = 380  # EfficientNet-B4 input size
CLASSIFICATION_THRESHOLD = settings.ml_classification_threshold

# Defect detection threshold
DEFECT_THRESHOLD = settings.ml_defect_threshold

# A/B testing
AB_TEST_PERCENTAGE = settings.ml_ab_test_percentage

# ImageNet class -> e-commerce category mapping
IMAGENET_TO_ECOMMERCE = {
    # Electronics
    "laptop": "electronics", "notebook": "electronics", "desktop_computer": "electronics",
    "monitor": "electronics", "screen": "electronics", "television": "electronics",
    "cellular_telephone": "electronics", "iPod": "electronics", "mouse": "electronics",
    "keyboard": "electronics", "remote_control": "electronics", "joystick": "electronics",
    "printer": "electronics", "modem": "electronics", "loudspeaker": "electronics",
    "microphone": "electronics", "headphone": "electronics",
    # Clothing
    "suit": "clothing", "jean": "clothing", "jersey": "clothing",
    "sweatshirt": "clothing", "cardigan": "clothing", "trench_coat": "clothing",
    "fur_coat": "clothing", "lab_coat": "clothing", "pajama": "clothing",
    "bikini": "clothing", "swimming_trunks": "clothing", "miniskirt": "clothing",
    "poncho": "clothing", "cloak": "clothing", "kimono": "clothing",
    # Footwear
    "running_shoe": "footwear", "loafer": "footwear", "sandal": "footwear",
    "boot": "footwear", "clog": "footwear", "cowboy_boot": "footwear",
    "shoe_shop": "footwear",
    # Furniture
    "desk": "furniture", "bookcase": "furniture", "filing_cabinet": "furniture",
    "table_lamp": "furniture", "rocking_chair": "furniture", "studio_couch": "furniture",
    "chiffonier": "furniture", "four-poster": "furniture", "wardrobe": "furniture",
    "dining_table": "furniture", "folding_chair": "furniture",
    # Jewelry
    "necklace": "jewelry", "ring": "jewelry", "bracelet": "jewelry",
    # Sports
    "basketball": "sports", "soccer_ball": "sports", "baseball": "sports",
    "tennis_ball": "sports", "golf_ball": "sports", "ping-pong_ball": "sports",
    "ski": "sports", "snowboard": "sports", "surfboard": "sports",
    "racket": "sports", "dumbbell": "sports",
    # Home & Garden
    "vase": "home_garden", "pot": "home_garden", "flowerpot": "home_garden",
    "pillow": "home_garden", "quilt": "home_garden", "shower_curtain": "home_garden",
    "doormat": "home_garden", "wall_clock": "home_garden",
    # Automotive
    "car_wheel": "automotive", "sports_car": "automotive", "convertible": "automotive",
    "minivan": "automotive", "pickup": "automotive",
    # Toys
    "teddy": "toys", "jigsaw_puzzle": "toys", "toy_shop": "toys",
}

# Color names for attribute extraction
COLOR_NAMES = [
    "red", "blue", "green", "yellow", "orange", "purple",
    "pink", "brown", "black", "white", "gray", "beige",
]

# Material names
MATERIAL_NAMES = [
    "leather", "metal", "wood", "plastic", "fabric",
    "glass", "ceramic", "rubber",
]

# Condition levels
CONDITION_LEVELS = ["new", "like_new", "good", "fair", "poor"]
