import streamlit as st
import pandas as pd
import bcrypt
import os
import aiml

# Path for user credentials file
credentials_file = 'users.csv'

# Function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Function to verify password
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Function to load user credentials
def load_users():
    if os.path.exists(credentials_file):
        return pd.read_csv(credentials_file)
    else:
        # Create the file if it doesn't exist
        df = pd.DataFrame(columns=["username", "password"])
        df.to_csv(credentials_file, index=False)
        return df

# Function to save a new user
def save_user(username, password):
    users_df = load_users()
    new_user = pd.DataFrame({"username": [username], "password": [hash_password(password)]})
    updated_users = pd.concat([users_df, new_user], ignore_index=True)
    updated_users.to_csv(credentials_file, index=False)

# Login Function
def login_user(username, password):
    users_df = load_users()
    user_record = users_df[users_df['username'] == username]
    if not user_record.empty and verify_password(password, user_record.iloc[0]['password']):
        return True
    else:
        return False

# Registration Function
def register_user(username, password):
    users_df = load_users()
    if username in users_df['username'].values:
        st.warning("Username already taken. Please choose another.")
    else:
        save_user(username, password)
        st.success("Registration successful! You can now log in.")

# Initialize session state for login status
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Streamlit Login / Register Form
st.sidebar.title("Nutrimate Login")

login_tab, register_tab = st.sidebar.tabs(["Login", "Register"])

# Handle login
with login_tab:
    st.write("Log in to access Nutrimate.")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    login_button = st.button("Log in")

    if login_button:
        if login_user(username, password):
            st.success(f"Welcome, {username}!")
            st.session_state.logged_in = True
            st.session_state.current_user = username
        else:
            st.error("Invalid username or password.")

# Handle registration
with register_tab:
    st.write("Create a new Nutrimate account.")
    new_username = st.text_input("New Username", key="register_username")
    new_password = st.text_input("New Password", type="password", key="register_password")
    register_button = st.button("Register")

    if register_button:
        if new_username and new_password:
            register_user(new_username, new_password)
        else:
            st.warning("Please fill in both fields.")


# Main app content - only accessible when logged in
if st.session_state.logged_in:

    # Load and preprocess the dataset
    recipes_13k_df = pd.read_csv('13k-recipes-complete-updated.csv')
    recipes_13k_df.columns = recipes_13k_df.columns.str.strip()
    recipes_13k_df['Cleaned_Ingredients'] = recipes_13k_df['Cleaned_Ingredients'].fillna('')
    recipes_13k_df['Title'] = recipes_13k_df['Title'].fillna('')
    recipes_13k_df['Instructions'] = recipes_13k_df['Instructions'].fillna('')


    dietary_columns = ['Vegan', 'Vegetarian', 'Gluten_Free', 'Lactose_Free', 'Non_Vegetarian']
    for col in dietary_columns:
        recipes_13k_df[col] = recipes_13k_df[col].apply(lambda x: True if str(x).lower() == 'true' else False)

    # Fill missing values in dietary columns with False
    recipes_13k_df[dietary_columns] = recipes_13k_df[dietary_columns].fillna(False)

# Ingredient categories
ingredient_categories = {
    'meat_products': ['chicken', 'beef', 'pork', 'lamb', 'bacon', 'sausage', 'fish', 'seafood', 'shrimp', 'turkey',
                      'ham', 'veal', 'duck', 'goat', 'crab', 'lobster', 'tuna', 'salmon', 'anchovy', 'prosciutto',
                      'salami', 'chorizo'],
    'dairy_products': ['milk', 'cheese', 'cream', 'butter', 'yogurt', 'whey', 'ricotta', 'mozzarella', 'parmesan',
                       'cheddar', 'buttermilk', 'sour cream', 'mascarpone', 'ghee', 'half and half', 'heavy cream'],
    'gluten_products': ['wheat', 'flour', 'pasta', 'bread', 'barley', 'rye', 'couscous', 'semolina', 'farro',
                        'breadcrumbs', 'noodles', 'spaghetti', 'macaroni', 'crackers'],
    'eggs': ['egg', 'eggs', 'egg white', 'egg yolk', 'egg whites', 'egg yolks'],
    'seafood': ['fish', 'shrimp', 'crab', 'lobster', 'clam', 'mussel', 'oyster', 'scallop', 'squid', 'octopus'],
    'nuts_seeds': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'peanut', 'sesame', 'pine nut', 'chia',
                   'flaxseed'],
    'vegetables': ['onion', 'garlic', 'tomato', 'carrot', 'celery', 'pepper', 'lettuce', 'spinach', 'broccoli',
                   'cauliflower'],
    'fruits': ['apple', 'banana', 'orange', 'lemon', 'lime', 'berry', 'strawberry', 'blueberry', 'raspberry', 'grape'],
    'grains': ['rice', 'quinoa', 'oat', 'corn', 'millet', 'buckwheat', 'amaranth', 'wild rice'],
    'legumes': ['bean', 'lentil', 'chickpea', 'pea', 'soybean', 'tofu', 'tempeh'],
    'herbs_spices': ['basil', 'oregano', 'thyme', 'rosemary', 'cumin', 'coriander', 'paprika', 'cinnamon', 'nutmeg',
                     'ginger'],
    'sweeteners': ['sugar', 'honey', 'maple syrup', 'agave', 'stevia', 'molasses', 'corn syrup'],
    'oils': ['olive oil', 'vegetable oil', 'coconut oil', 'sesame oil', 'canola oil', 'sunflower oil'],
    'alcoholic': ['wine', 'beer', 'vodka', 'rum', 'whiskey', 'brandy', 'sherry', 'cognac']
}

# Function to filter recipes based on dietary preferences, allergens, and ingredient categories
def filter_by_preferences(df, dietary_preferences, allergens, include_category, exclude_category):
    if dietary_preferences.get('Vegan', False):
        df = df[~df['Cleaned_Ingredients'].str.contains('|'.join(ingredient_categories['dairy_products']), case=False,
                                                        na=False)]
        df = df[df['Vegan'] == True]

    if dietary_preferences.get('Vegetarian', False):
        df = df[df['Vegetarian'] == True]

    if dietary_preferences.get('Gluten-Free', False):
        df = df[df['Gluten_Free'] == True]

    if dietary_preferences.get('Lactose-Free', False):
        df = df[df['Lactose_Free'] == True]

    if dietary_preferences.get('Non-Vegetarian', False):
        df = df[(df['Vegetarian'] == False) & (df['Vegan'] == False)]

    for allergen in allergens:
        df = df[~df['Cleaned_Ingredients'].str.contains(allergen, case=False, na=False)]

    if include_category:
        included_ingredients = []
        for category in include_category:
            included_ingredients.extend(ingredient_categories[category])
        included_ingredients = [ingredient.lower() for ingredient in included_ingredients]
        df = df[df['Cleaned_Ingredients'].apply(
            lambda x: any(ingredient in x.lower() for ingredient in included_ingredients))]

    if exclude_category:
        excluded_ingredients = []
        for category in exclude_category:
            excluded_ingredients.extend(ingredient_categories[category])
        excluded_ingredients = [ingredient.lower() for ingredient in excluded_ingredients]
        df = df[~df['Cleaned_Ingredients'].apply(
            lambda x: any(ingredient in x.lower() for ingredient in excluded_ingredients))]

    return df

# Streamlit App - Custom Styling
st.markdown("""
    <style>
    .main-title {
        color: #F4A300;
        font-size: 36px;
        font-weight: bold;
        text-align: center;
    }
    .subheader {
        color: #2E8B57;
        font-size: 24px;
        text-align: center;
    }
    .button {
        background-color: #F4A300;
        color: white;
        font-size: 18px;
    }
    .button:hover {
        background-color: #FF6F00;
    }
    body {
        background-color: #F0F8FF;
    }
    .recommendation-card {
        background-color: #FFF3E0;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 10px;
        font-family: "Comic Sans MS", cursive, sans-serif;
    }
    .recipe-title {
        font-size: 24px;
        color: #FF6F00;
        font-weight: bold;
    }
    .recipe-ingredients, .recipe-instructions, .recipe-nutrition {
        font-size: 18px;
        color: #555555;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🍽 Nutrimate - Recipe Recommender 🍴</p>', unsafe_allow_html=True)

# Display a logo or image (optional)
st.image("image.jpeg",
         width=200)

# Typical health app questions in columns
col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age", min_value=1, max_value=120, value=25)
    height = st.number_input("Height (cm)", min_value=50, max_value=250, value=170)
with col2:
    weight = st.number_input("Weight (kg)", min_value=10, max_value=200, value=70)
    activity_level = st.selectbox("Activity Level", ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"])

# Input fields for dietary preferences and allergens in columns
gender = st.selectbox("Gender", ["Male", "Female"])

kernal = aiml.Kernel()

# Load AIML file
faq_file = "faq.aiml"
if not os.path.exists(faq_file):
    raise FileNotFoundError(f"AIML file {faq_file} not found!")
kernal.learn(faq_file)


# Dropdown for selecting category
category = st.selectbox(
    "Select a Category",
    ("Weight Loss", "Weight Gain", "Fitness", "General Health")
)

# Map the selected category to the corresponding AIML pattern
if category == "Weight Loss":
    query = "IMPORTANT INGREDIENTS FOR WEIGHT LOSS"
elif category == "Weight Gain":
    query = "IMPORTANT INGREDIENTS FOR WEIGHT GAIN"
elif category == "Fitness":
    query = "IMPORTANT INGREDIENTS FOR FITNESS"
elif category == "General Health":
    query = "IMPORTANT INGREDIENTS FOR GENERAL HEALTH"

# Get AIML response
response = kernal.respond(query)

# Display AIML-generated answer
st.subheader(f"FAQ: {category}")
st.write(response)

preferred_ingredient = st.text_input("Preferred ingredient (e.g., chicken, spinach, etc.)")


# Ingredient categories for inclusion and exclusion
st.subheader("Ingredient Category Filters")
include_category = st.multiselect("Select Categories to Include", list(ingredient_categories.keys()))
exclude_category = st.multiselect("Select Categories to Exclude", list(ingredient_categories.keys()))

st.subheader("Select Dietary Preference")

dietary_preferences = {
    'Vegan': st.checkbox('Vegan'),
    'Vegetarian': st.checkbox('Vegetarian'),
    'Gluten-Free': st.checkbox('Gluten-Free'),
    'Lactose-Free': st.checkbox('Lactose-Free'),
    'Non-Vegetarian': st.checkbox('Non-Vegetarian')
}

allergens = st.multiselect('Select allergens to avoid', ['Nuts', 'Dairy', 'Eggs', 'Soy', 'Wheat'])

# Button to generate recommendations
if st.button("Get Recipe Recommendations", key="recommend"):
    try:
        # Filter by preferred ingredient
        if preferred_ingredient:
            filtered_df = recipes_13k_df[
                recipes_13k_df['Cleaned_Ingredients'].str.contains(preferred_ingredient, case=False, na=False)]
        else:
            filtered_df = recipes_13k_df

        # Filter by dietary preferences, allergens, and ingredient categories
        filtered_df = filter_by_preferences(filtered_df, dietary_preferences, allergens, include_category,
                                            exclude_category)

        # If no recipes are found, return an error
        if filtered_df.empty:
            st.error("No suitable recipes found based on your inputs.")
        else:
            st.subheader("Recommended Recipes:")
            for index, row in filtered_df.iterrows():
                st.markdown(
                    f'<div class="recommendation-card">'
                    f'<p class="recipe-title">{row["Title"]}</p>'
                    f'<p class="recipe-ingredients">Ingredients: {row["Cleaned_Ingredients"]}</p>'
                    f'<p class="recipe-instructions">Instructions: {row["Instructions"]}</p>'
                    f'<p class="recipe-nutrition">Estimated Calories: {row["Estimated_Calories"]} kcal</p>'
                    f'<p class="recipe-nutrition">Healthiness Score: {row["Healthiness_Score"]}</p>'
                    f'<p class="recipe-nutrition">Calories: {row["calories"]} kcal</p>'
                    f'<p class="recipe-nutrition">Protein: {row["protein"]} g</p>'
                    f'<p class="recipe-nutrition">Fat: {row["fat"]} g</p>'
                    f'</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"An error occurred: {e}")

#else:
 #   st.warning("Please log in to access the Nutrimate app.")