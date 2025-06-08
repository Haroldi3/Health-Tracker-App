import streamlit as st
import pandas as pd
import datetime
import requests
import pydeck as pdk

# API Key
API_NINJAS_KEY = "XlXxN289UTSaz6Rpa66AEw==fQk9fh0DeCf7TIQ0"

today = datetime.date.today()

# Set up
if 'profile' not in st.session_state:
    st.session_state.profile = {}

if 'nutrition_log' not in st.session_state:
    st.session_state.nutrition_log = pd.DataFrame(columns=['Date', 'Calories (kcal)', 'Water (oz)', 'Weight (lbs)'])

if 'cardio_log' not in st.session_state:
    st.session_state.cardio_log = pd.DataFrame(columns=['Date', 'Duration (min)', 'Distance (miles)', 'Activity Type', 'Calories Burned', 'Coordinates'])

if 'strength_log' not in st.session_state:
    st.session_state.strength_log = pd.DataFrame(columns=['Date', 'Muscle Group', 'Exercise', 'Weight (lbs)', 'Sets', 'Reps'])

if 'daily_totals' not in st.session_state:
    st.session_state.daily_totals = {}

if today not in st.session_state.daily_totals:
    st.session_state.daily_totals[today] = {'Calories (kcal)': 0, 'Water (oz)': 0, 'Weight (lbs)': 50.0}

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([ "👤 Profile",
                                         "🥗 Nutrition",
                                         "🏃 Cardio",
                                         "🏋️ Strength",
                                         "📊 Progress"
                                         ])

#TAB 1: Profile Setup
with tab1:
    st.header("👤 Profile Setup")
# Maintenance calorie intake Formula
    def calculate_bmr(weight_lbs, height_in, age, gender):
        weight_kg = weight_lbs * 0.453592
        height_cm = height_in * 2.54
        gender_const = 5 if gender == "Male" else -161
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + gender_const

    def calculate_tdee(bmr, activity_level):
        factors = {"Sedentary": 1.2, "Lightly Active": 1.375, "Moderately Active": 1.55, "Very Active": 1.725, "Extremely Active": 1.9}
        return bmr * factors[activity_level]
# Maintenance calorie intake calculated to achieve goal selected by user
    def adjust_calories(tdee, goal):
        if goal == "Lose Weight": return tdee * 0.85
        elif goal == "Gain Weight": return tdee * 1.15
        else: return tdee
# User Input required to create a profile
    with st.form("profile_form"):
        name = st.text_input("Name:")
        gender = st.radio("Gender:", ["Male", "Female"])
        age = st.number_input("Age:", min_value=10, max_value=100, value=20)
        height_in = st.number_input("Height (inches):", min_value=48.0, max_value=96.0, value=65.0)
        weight_lbs = st.number_input("Weight (lbs):", min_value=50.0, max_value=600.0, value=150.0)
        activity = st.selectbox("Activity Level:", ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"])
        goal = st.selectbox("Goal:", ["Maintain Weight", "Lose Weight", "Gain Weight"])
        submit = st.form_submit_button("Calculate")

    if submit:
        bmr = calculate_bmr(weight_lbs, height_in, age, gender)
        tdee = calculate_tdee(bmr, activity)
        target_calories = adjust_calories(tdee, goal)

        st.success(f"🎯 Daily Calorie Goal: {round(target_calories)} kcal/day")

        st.session_state.profile = {
            'name': name, 'gender': gender, 'age': age,
            'height_in': height_in, 'weight_lbs': weight_lbs,
            'bmr': round(bmr), 'tdee': round(tdee),
            'goal': goal, 'target_calories': round(target_calories)
        }

    if st.session_state.profile:
        st.write("✅ Your Profile Info:")
        st.json(st.session_state.profile)

# Tab 2: Nutrition Logging
with tab2:
    st.header("🥗 Nutrition Logging")
# User Input here
    with st.form("nutrition_form"):
        calories = st.number_input("Calories Consumed (kcal):", min_value=0.0, max_value=10000.0, value=0.0)
        water = st.number_input("Water Intake (oz):", min_value=0.0, max_value=200.0, value=0.0)
        weight = st.number_input("Today's Weight (lbs):", min_value=50.0, max_value=600.0, value=50.0)
        submit = st.form_submit_button("Log Entry")
#
    if submit:
        st.session_state.daily_totals[today]['Calories (kcal)'] += calories
        st.session_state.daily_totals[today]['Water (oz)'] += water
        st.session_state.daily_totals[today]['Weight (lbs)'] = weight
        st.success("Entry logged!")

    # Demonstrate a Sidebar visible through-out the whole website
    st.sidebar.header("📊 Daily Progress")

    target_water = 120
    water_now = st.session_state.daily_totals[today]['Water (oz)']
    st.sidebar.subheader("💧 Water Intake")
    st.sidebar.progress(min(int((water_now / target_water) * 100), 100), text=f"{water_now} oz / {target_water} oz")

    calorie_goal = st.session_state.profile.get('target_calories', 2500)
    calories_now = st.session_state.daily_totals[today]['Calories (kcal)']
    st.sidebar.subheader("🔥 Calories Consumed")
    st.sidebar.progress(min(int((calories_now / calorie_goal) * 100), 100), text=f"{calories_now} kcal / {calorie_goal} kcal")

# Tab 3: Cardio Logging
with tab3:
    st.header("🏃 Cardio Logging")

# Form To add cardio
    with st.form("cardio_form"):
        city = st.text_input("Enter City:")
        distance = st.number_input("Distance (miles):", min_value=0.0, value=0.0)
        duration = st.number_input("Duration (minutes):", min_value=0.0, value=0.0)
        activity = st.selectbox("Activity Type:", ["running", "walking", "cycling", "swimming", "rowing"])
        submit = st.form_submit_button("Log Cardio")

    if submit:
        # Call CaloriesBurned API
        api_url = "https://api.api-ninjas.com/v1/caloriesburned"
        params = {'activity': activity, 'duration': duration}
        headers = {'X-Api-Key': API_NINJAS_KEY}
        response = requests.get(api_url, params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            calories_burned = data[0]['total_calories'] if data else 0
            st.success(f"Calories burned: {calories_burned} kcal")
            entry = pd.DataFrame([{
                'Date': today, 'Duration (min)': duration, 'Distance (miles)': distance, 'Activity Type': activity,
                'Calories Burned': calories_burned, 'Location': city
            }])
            st.session_state.cardio_log = pd.concat([st.session_state.cardio_log, entry], ignore_index=True)

        else:
            st.error("API request failed!")

    # Recommendations Sections for Running and Biking in South Florida
    st.subheader("🗺️ Suggested Nearby Routes")
    rec_activity = st.selectbox("Choose Activity for Suggestions:", ["running", "biking", "walking"])
    # Information From https://www.miamidade.gov/global/recreation/parksmasterplan/bike-trail-maps.page
    if rec_activity == "biking":
        demo_data = pd.DataFrame({
            'lat': [25.970, 25.730, 25.726, 25.662, 25.585, 25.565, 25.499, 25.425, 25.855],
            'lon': [-80.189, -80.162, -80.242, -80.282, -80.345, -80.386, -80.468, -80.498, -80.278]
        })
        st.write("🚴 Recommended Bike Trails:")
        st.write("""
            - Snake Creek Trail (paved)
            - Rickenbacker Trail (paved)
            - Commodore Trail (paved)
            - Old Cutler Trail (paved)
            - Biscayne Trail (paved and dirt)
            - Black Creek Trail (paved and dirt)
            - Biscayne-Everglades Greenway (gravel or rocks)
            - Southern Glades Trail (gravel or rocks)
            - Amelia Trail
            """)
        st.write("🚴 Recommended Bike Trails near Miami")

    elif rec_activity == "running":
        # Information from https://www.mapmyrun.com/us/miami-fl/
        demo_data = pd.DataFrame({
            'lat': [26.122, 26.011, 26.100, 25.727, 25.728, 25.822, 25.742, 25.774],
            'lon': [-80.105, -80.149, -80.401, -80.270, -80.272, -80.289, -80.272, -80.193]
        })
        st.write("🏃 Recommended Running Routes:")
        st.write("""
            - Ft Lauderdale Beach 14M Run
            - Hollywood Half Marathon
            - Weston Park Run
            - Coral Gables 8 M Run
            - Coral Gables 7 M Run
            - Miami Springs Loop
            - Granada Golf Course Loop
            - Miami Marathon Start Line Route
            """)
        st.write("🏃 Recommended Running Tracks near Miami")

    st.map(demo_data)

# Tab 4: Strength Logging
with tab4:
    st.header("🏋️ Strength Logging")

    if 'workout_session' not in st.session_state:
        st.session_state.workout_session = []
    # Pick a Muscle group
    muscle = st.selectbox("Select Muscle Group:", [
        "", "abdominals", "biceps", "chest", "triceps", "quadriceps",
        "hamstrings", "lats", "glutes", "calves", "forearms",
        "shoulders", "middle_back", "lower_back"
    ])
    # After picking a muscle group, you are prompted with several workouts revolving the muscle chosen
    exercises = []
    if muscle:
        api_url = f"https://api.api-ninjas.com/v1/exercises?muscle={muscle}"
        response = requests.get(api_url, headers={'X-Api-Key': API_NINJAS_KEY})
        if response.status_code == 200:
            exercises = [ex['name'] for ex in response.json()]

    if muscle:
        with st.form("add_exercise_form"):
            exercise = st.selectbox("Select Exercise:", exercises)
            weight_used = st.number_input("Weight Used (lbs):", min_value=0.0)
            sets = st.number_input("Sets:", min_value=1)
            reps = st.number_input("Reps per Set:", min_value=1)
            add_button = st.form_submit_button("Add Exercise")

        if add_button:
            st.session_state.workout_session.append({
                'Date': today, 'Muscle Group': muscle, 'Exercise': exercise,
                'Weight (lbs)': weight_used, 'Sets': sets, 'Reps': reps
            })
            st.success("Exercise added to session!")

    # Creates a list of active workouts
    if st.session_state.workout_session:
        st.subheader("Current Workout Session:")
        st.dataframe(pd.DataFrame(st.session_state.workout_session))

        if st.button("Save Full Workout"):
            full_entry = pd.DataFrame(st.session_state.workout_session)
            st.session_state.strength_log = pd.concat([st.session_state.strength_log, full_entry], ignore_index=True)
            st.success("Full workout session saved!")
            st.session_state.workout_session = []

# Tab 5: Progress Overview
with tab5:
    st.header("📊 Progress Overview")
    # Creates a Bar and Line chart based on the progress stated by the user/ progress is measured through weight and calorie intake
    if st.session_state.daily_totals:
        progress_df = pd.DataFrame.from_dict(st.session_state.daily_totals, orient="index")
        progress_df.index = pd.to_datetime(progress_df.index)
        st.subheader("📈 Weight Progress (Line Chart)")
        st.line_chart(progress_df['Weight (lbs)'])
        st.subheader("📊 Calorie Intake (Bar Chart)")
        st.bar_chart(progress_df['Calories (kcal)'])
    else:
        st.info("No nutrition data yet.")

