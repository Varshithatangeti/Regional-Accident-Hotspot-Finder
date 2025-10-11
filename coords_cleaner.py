import pandas as pd
import unicodedata
from difflib import get_close_matches

# ----------------------------------------------------
# 🧩 Helper: Normalize strings (remove accents, spaces)
# ----------------------------------------------------
def normalize(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s

# ----------------------------------------------------
# 📂 STEP 1: Load your coordinates dataset
# ----------------------------------------------------
coords_df = pd.read_csv("city_coordinates.csv")  # make sure this file exists
print(f"Loaded {len(coords_df)} rows from coordinate file.")

# Expected columns: ["City Name", "Latitude", "Longitude"]
# If columns differ, rename them here
# coords_df.rename(columns={"city": "City Name", "lat": "Latitude", "lon": "Longitude"}, inplace=True)

# ----------------------------------------------------
# 🧹 STEP 2: Normalize city names
# ----------------------------------------------------
coords_df["City_norm"] = coords_df["City Name"].apply(normalize)

# ----------------------------------------------------
# 🔍 STEP 3: Detect and display duplicates
# ----------------------------------------------------
dupes = coords_df[coords_df.duplicated(subset="City_norm", keep=False)]
if not dupes.empty:
    print("\n⚠️ Duplicate cities found — merging by averaging coordinates:\n")
    print(dupes.sort_values("City_norm")[["City Name", "Latitude", "Longitude"]])

# ----------------------------------------------------
# 🧮 STEP 4: Merge duplicates (average coordinates)
# ----------------------------------------------------
coords_df = (
    coords_df.groupby("City_norm", as_index=False)
    .agg({
        "Latitude": "mean",
        "Longitude": "mean",
        "City Name": "first"
    })
)
print(f"\n✅ Cleaned coordinate data: {len(coords_df)} unique cities remain.")

# ----------------------------------------------------
# 🗺️ STEP 5: Build city lookup dictionary
# ----------------------------------------------------
coords_lookup = (
    coords_df.set_index("City_norm")[["Latitude", "Longitude", "City Name"]]
    .to_dict(orient="index")
)
print(f"✅ City coordinate lookup dictionary ready ({len(coords_lookup)} entries).")

# ----------------------------------------------------
# 💾 STEP 6: Save cleaned version
# ----------------------------------------------------
coords_df.to_csv("cleaned_city_coordinates.csv", index=False)
print("💾 Cleaned coordinates saved to 'cleaned_city_coordinates.csv'.")

# ----------------------------------------------------
# 🔎 STEP 7: Lookup function with fuzzy suggestions
# ----------------------------------------------------
def get_city_coordinates(city_name):
    norm_city = normalize(city_name)
    if norm_city in coords_lookup:
        return coords_lookup[norm_city]
    else:
        # fuzzy matching
        closest = get_close_matches(norm_city, coords_lookup.keys(), n=3, cutoff=0.6)
        if closest:
            suggestions = [coords_lookup[c]["City Name"] for c in closest]
            return f"Cannot find '{city_name}'. Did you mean: {suggestions}?"
        else:
            return f"Cannot find coordinates for: {city_name}"

# ----------------------------------------------------
# ✅ Example usage
# ----------------------------------------------------
example_city = "Farward Kahuta"
result = get_city_coordinates(example_city)
print(f"\n📍 Lookup result for '{example_city}': {result}")
