import pandas as pd

# Read IN.txt
# Geonames files are usually tab-separated
df = pd.read_csv("IN.txt", sep="\t", header=None, dtype=str, on_bad_lines='skip')

# Select relevant columns
# Adjust based on your data sample: 
# City Name = column 2 (index 1) or 3 (index 2), Latitude = index 4, Longitude = index 5
df_coords = df.iloc[:, [2, 4, 5]]
df_coords.columns = ["City Name", "Latitude", "Longitude"]

# Remove rows with missing Latitude or Longitude
df_coords = df_coords[df_coords["Latitude"].notna() & df_coords["Longitude"].notna()]

# Keep only numeric Latitude/Longitude
df_coords = df_coords[df_coords["Latitude"].str.match(r'^-?\d+(\.\d+)?$')]
df_coords = df_coords[df_coords["Longitude"].str.match(r'^-?\d+(\.\d+)?$')]

# Strip spaces from city names
df_coords["City Name"] = df_coords["City Name"].str.strip()

# Drop duplicates
df_coords = df_coords.drop_duplicates(subset=["City Name"])

# Save to CSV
df_coords.to_csv("city_coordinates.csv", index=False)
print("✅ city_coordinates.csv created successfully!")
