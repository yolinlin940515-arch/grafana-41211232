"""
Process the Excel data into JSON files for the dashboard.
Generates aggregated data for each analysis dimension.
"""
import pandas as pd
import json
import os
import sys

EXCEL_PATH = r'C:\Users\HTL22\Downloads\grafana-main41211232\亞洲旅館真實館名與模擬營運資料.xlsx'
OUTPUT_DIR = r'C:\Users\HTL22\Downloads\grafana-main41211232\hotel-dashboard\data'

print("Reading Excel file...", flush=True)
df = pd.read_excel(EXCEL_PATH, sheet_name='逐館逐日資料與紀錄', header=8)

# Rename columns to English-friendly short names
col_map = {
    '情境代碼': 'scenario_code',
    '系統旅館名稱': 'hotel_name',
    '國家／地區': 'country',
    '真實城市／市場': 'city',
    '入住日期': 'date',
    '星期': 'weekday',
    '週末': 'is_weekend',
    '當地假日': 'is_holiday',
    '節日名稱（含補假）': 'holiday_name',
    '市場定位〔模〕': 'market_position',
    '客房總數〔模〕': 'total_rooms',
    '規模組〔模〕': 'size_group',
    '距市中心 km〔模〕': 'distance_km',
    '設施分數 1–10〔模〕': 'facility_score',
    '商務客比率〔模〕': 'business_ratio',
    '幣別': 'currency',
    '每晚房價〔模〕': 'room_price',
    '價格指數（基價=100）': 'price_index',
    '售出房間數〔模〕': 'rooms_sold',
    '住房率〔模〕': 'occupancy_rate',
    '市場基價〔假設〕': 'base_price',
    '館別價格係數': 'hotel_price_coeff',
    '週末調整率': 'weekend_adj',
    '假日調整率': 'holiday_adj',
    '當日價格係數': 'daily_price_coeff',
    '資料版本': 'data_version',
    '名冊旅館 ID': 'hotel_id',
    '名冊地點（原文）': 'location_en',
    '館內情境序號': 'scenario_seq',
    '原版市場（對帳）': 'original_market',
}
df.rename(columns=col_map, inplace=True)

# Filter primary scenario (scenario_seq == 1)
df_primary = df[df['scenario_seq'] == 1].copy()
df_primary['date_str'] = df_primary['date'].dt.strftime('%Y-%m-%d')
df_primary['unsold_rooms'] = df_primary['total_rooms'] - df_primary['rooms_sold']
df_primary['daily_revenue'] = df_primary['room_price'] * df_primary['rooms_sold']

print(f"Primary scenario rows: {len(df_primary)}", flush=True)

# ============ 1. Overview KPIs ============
print("Generating overview data...", flush=True)
overview = {
    'total_records': int(len(df)),
    'primary_records': int(len(df_primary)),
    'countries': int(df_primary['country'].nunique()),
    'hotels': int(df_primary['hotel_name'].nunique()),
    'cities': int(df_primary['city'].nunique()),
    'date_range': {'start': '2026-10-01', 'end': '2026-10-31'},
    'avg_occupancy': round(float(df_primary['occupancy_rate'].mean()), 4),
    'avg_price_index': round(float(df_primary['price_index'].mean()), 2),
    'total_rooms_sold': int(df_primary['rooms_sold'].sum()),
    'total_unsold': int(df_primary['unsold_rooms'].sum()),
}

# Country summary
country_summary = []
for country, grp in df_primary.groupby('country'):
    country_summary.append({
        'country': country,
        'hotels': int(grp['hotel_name'].nunique()),
        'avg_occupancy': round(float(grp['occupancy_rate'].mean()), 4),
        'avg_price_index': round(float(grp['price_index'].mean()), 2),
        'avg_room_price': round(float(grp['room_price'].mean()), 0),
        'total_rooms_sold': int(grp['rooms_sold'].sum()),
        'total_unsold': int(grp['unsold_rooms'].sum()),
        'avg_facility_score': round(float(grp['facility_score'].mean()), 2),
        'currency': grp['currency'].iloc[0],
    })
overview['countries_data'] = country_summary

with open(os.path.join(OUTPUT_DIR, 'overview.json'), 'w', encoding='utf-8') as f:
    json.dump(overview, f, ensure_ascii=False, indent=2)

# ============ 2. Cost Analysis: Size Group vs Unsold Rooms ============
print("Generating cost analysis data...", flush=True)
cost_data = {}

# 2a. Size group comparison
size_group_data = []
for sg, grp in df_primary.groupby('size_group'):
    size_group_data.append({
        'size_group': sg,
        'avg_total_rooms': round(float(grp['total_rooms'].mean()), 1),
        'avg_rooms_sold': round(float(grp['rooms_sold'].mean()), 1),
        'avg_unsold': round(float(grp['unsold_rooms'].mean()), 1),
        'avg_occupancy': round(float(grp['occupancy_rate'].mean()), 4),
        'avg_revenue': round(float(grp['daily_revenue'].mean()), 0),
        'hotels': int(grp['hotel_name'].nunique()),
    })
cost_data['size_groups'] = size_group_data

# 2b. Per hotel unsold rooms (top/bottom)
hotel_unsold = df_primary.groupby('hotel_name').agg(
    avg_unsold=('unsold_rooms', 'mean'),
    avg_occupancy=('occupancy_rate', 'mean'),
    total_rooms=('total_rooms', 'first'),
    country=('country', 'first'),
    city=('city', 'first'),
    size_group=('size_group', 'first'),
).reset_index()
hotel_unsold['avg_unsold'] = hotel_unsold['avg_unsold'].round(1)
hotel_unsold['avg_occupancy'] = hotel_unsold['avg_occupancy'].round(4)
hotel_unsold = hotel_unsold.sort_values('avg_unsold', ascending=False)

cost_data['top_unsold'] = hotel_unsold.head(20).to_dict(orient='records')
cost_data['bottom_unsold'] = hotel_unsold.tail(20).to_dict(orient='records')

# 2c. Daily trend of unsold rooms by size group
daily_size = df_primary.groupby(['date_str', 'size_group']).agg(
    avg_unsold=('unsold_rooms', 'mean'),
    avg_occupancy=('occupancy_rate', 'mean'),
).reset_index()
daily_size['avg_unsold'] = daily_size['avg_unsold'].round(1)
daily_size['avg_occupancy'] = daily_size['avg_occupancy'].round(4)
cost_data['daily_by_size'] = daily_size.to_dict(orient='records')

with open(os.path.join(OUTPUT_DIR, 'cost_analysis.json'), 'w', encoding='utf-8') as f:
    json.dump(cost_data, f, ensure_ascii=False, indent=2)

# ============ 3. Facility Investment vs Returns ============
print("Generating facility analysis data...", flush=True)
facility_data = {}

# 3a. Facility score vs price scatter
hotel_facility = df_primary.groupby('hotel_name').agg(
    facility_score=('facility_score', 'first'),
    avg_price=('room_price', 'mean'),
    avg_price_index=('price_index', 'mean'),
    avg_occupancy=('occupancy_rate', 'mean'),
    country=('country', 'first'),
    city=('city', 'first'),
    size_group=('size_group', 'first'),
    market_position=('market_position', 'first'),
).reset_index()
hotel_facility['avg_price'] = hotel_facility['avg_price'].round(0)
hotel_facility['avg_price_index'] = hotel_facility['avg_price_index'].round(2)
hotel_facility['avg_occupancy'] = hotel_facility['avg_occupancy'].round(4)
facility_data['hotel_scatter'] = hotel_facility.to_dict(orient='records')

# 3b. Facility score bins
bins = [0, 3, 5, 7, 10]
labels = ['1-3 低', '4-5 中低', '6-7 中高', '8-10 高']
df_primary['facility_bin'] = pd.cut(df_primary['facility_score'], bins=bins, labels=labels)
facility_bins = []
for b, grp in df_primary.groupby('facility_bin', observed=True):
    facility_bins.append({
        'bin': str(b),
        'avg_price_index': round(float(grp['price_index'].mean()), 2),
        'avg_occupancy': round(float(grp['occupancy_rate'].mean()), 4),
        'hotels': int(grp['hotel_name'].nunique()),
        'avg_room_price': round(float(grp['room_price'].mean()), 0),
    })
facility_data['facility_bins'] = facility_bins

with open(os.path.join(OUTPUT_DIR, 'facility_analysis.json'), 'w', encoding='utf-8') as f:
    json.dump(facility_data, f, ensure_ascii=False, indent=2)

# ============ 4. Location/Distance Analysis ============
print("Generating location analysis data...", flush=True)
location_data = {}

# 4a. Distance vs price scatter per hotel
hotel_location = df_primary.groupby('hotel_name').agg(
    distance_km=('distance_km', 'first'),
    avg_price=('room_price', 'mean'),
    avg_price_index=('price_index', 'mean'),
    avg_occupancy=('occupancy_rate', 'mean'),
    country=('country', 'first'),
    city=('city', 'first'),
    size_group=('size_group', 'first'),
).reset_index()
hotel_location['avg_price'] = hotel_location['avg_price'].round(0)
hotel_location['avg_price_index'] = hotel_location['avg_price_index'].round(2)
hotel_location['avg_occupancy'] = hotel_location['avg_occupancy'].round(4)
location_data['hotel_scatter'] = hotel_location.to_dict(orient='records')

# 4b. Distance bins
dbins = [0, 3, 6, 10, 50]
dlabels = ['市中心(≤3km)', '近郊(3-6km)', '中距(6-10km)', '郊區(>10km)']
df_primary['dist_bin'] = pd.cut(df_primary['distance_km'], bins=dbins, labels=dlabels)
dist_bins = []
for b, grp in df_primary.groupby('dist_bin', observed=True):
    dist_bins.append({
        'bin': str(b),
        'avg_price_index': round(float(grp['price_index'].mean()), 2),
        'avg_occupancy': round(float(grp['occupancy_rate'].mean()), 4),
        'hotels': int(grp['hotel_name'].nunique()),
        'avg_room_price': round(float(grp['room_price'].mean()), 0),
    })
location_data['distance_bins'] = dist_bins

with open(os.path.join(OUTPUT_DIR, 'location_analysis.json'), 'w', encoding='utf-8') as f:
    json.dump(location_data, f, ensure_ascii=False, indent=2)

# ============ 5. Weekday/Holiday Analysis ============
print("Generating holiday analysis data...", flush=True)
holiday_data = {}

# 5a. Weekday vs Weekend vs Holiday comparison
day_types = []
# Weekdays (not weekend, not holiday)
wd = df_primary[(df_primary['is_weekend'] == 0) & (df_primary['is_holiday'] == 0)]
day_types.append({
    'type': '平日',
    'avg_price': round(float(wd['room_price'].mean()), 0),
    'avg_price_index': round(float(wd['price_index'].mean()), 2),
    'avg_occupancy': round(float(wd['occupancy_rate'].mean()), 4),
    'avg_rooms_sold': round(float(wd['rooms_sold'].mean()), 1),
    'records': int(len(wd)),
})
# Weekend only
we = df_primary[(df_primary['is_weekend'] == 1) & (df_primary['is_holiday'] == 0)]
day_types.append({
    'type': '週末',
    'avg_price': round(float(we['room_price'].mean()), 0),
    'avg_price_index': round(float(we['price_index'].mean()), 2),
    'avg_occupancy': round(float(we['occupancy_rate'].mean()), 4),
    'avg_rooms_sold': round(float(we['rooms_sold'].mean()), 1),
    'records': int(len(we)),
})
# Holiday
hol = df_primary[df_primary['is_holiday'] == 1]
day_types.append({
    'type': '國定假日',
    'avg_price': round(float(hol['room_price'].mean()), 0),
    'avg_price_index': round(float(hol['price_index'].mean()), 2),
    'avg_occupancy': round(float(hol['occupancy_rate'].mean()), 4),
    'avg_rooms_sold': round(float(hol['rooms_sold'].mean()), 1),
    'records': int(len(hol)),
})
holiday_data['day_types'] = day_types

# 5b. Daily trend
daily_trend = df_primary.groupby('date_str').agg(
    avg_price=('room_price', 'mean'),
    avg_price_index=('price_index', 'mean'),
    avg_occupancy=('occupancy_rate', 'mean'),
    total_sold=('rooms_sold', 'sum'),
    total_unsold=('unsold_rooms', 'sum'),
    is_weekend=('is_weekend', 'max'),
    is_holiday=('is_holiday', 'max'),
).reset_index()
daily_trend['avg_price'] = daily_trend['avg_price'].round(0)
daily_trend['avg_price_index'] = daily_trend['avg_price_index'].round(2)
daily_trend['avg_occupancy'] = daily_trend['avg_occupancy'].round(4)
holiday_data['daily_trend'] = daily_trend.to_dict(orient='records')

# 5c. Revenue efficiency: revenue per room by day type
revenue_eff = []
for dtype_name, grp in [('平日', wd), ('週末', we), ('國定假日', hol)]:
    rev_per_room = (grp['daily_revenue'] / grp['total_rooms']).mean()
    revenue_eff.append({
        'type': dtype_name,
        'avg_revenue_per_room': round(float(rev_per_room), 0),
        'avg_daily_revenue': round(float(grp['daily_revenue'].mean()), 0),
    })
holiday_data['revenue_efficiency'] = revenue_eff

# Holiday names
holiday_names = df_primary[df_primary['is_holiday'] == 1].groupby(['date_str', 'country']).agg(
    holiday_name=('holiday_name', 'first')
).reset_index()
holiday_data['holiday_names'] = holiday_names.to_dict(orient='records')

with open(os.path.join(OUTPUT_DIR, 'holiday_analysis.json'), 'w', encoding='utf-8') as f:
    json.dump(holiday_data, f, ensure_ascii=False, indent=2)

# ============ 6. Hotel Directory (for search/filter) ============
print("Generating hotel directory...", flush=True)
hotel_dir = df_primary.groupby('hotel_name').agg(
    hotel_id=('hotel_id', 'first'),
    country=('country', 'first'),
    city=('city', 'first'),
    location_en=('location_en', 'first'),
    market_position=('market_position', 'first'),
    total_rooms=('total_rooms', 'first'),
    size_group=('size_group', 'first'),
    distance_km=('distance_km', 'first'),
    facility_score=('facility_score', 'first'),
    business_ratio=('business_ratio', 'first'),
    currency=('currency', 'first'),
    avg_price=('room_price', 'mean'),
    avg_price_index=('price_index', 'mean'),
    avg_occupancy=('occupancy_rate', 'mean'),
    avg_rooms_sold=('rooms_sold', 'mean'),
    avg_unsold=('unsold_rooms', 'mean'),
    avg_revenue=('daily_revenue', 'mean'),
).reset_index()

for c in ['avg_price', 'avg_price_index', 'avg_rooms_sold', 'avg_unsold', 'avg_revenue']:
    hotel_dir[c] = hotel_dir[c].round(1)
hotel_dir['avg_occupancy'] = hotel_dir['avg_occupancy'].round(4)

hotel_dir_list = hotel_dir.sort_values('hotel_name').to_dict(orient='records')

with open(os.path.join(OUTPUT_DIR, 'hotel_directory.json'), 'w', encoding='utf-8') as f:
    json.dump(hotel_dir_list, f, ensure_ascii=False, indent=2)

# ============ 7. Country-level daily data ============
print("Generating country daily data...", flush=True)
country_daily = df_primary.groupby(['date_str', 'country']).agg(
    avg_occupancy=('occupancy_rate', 'mean'),
    avg_price_index=('price_index', 'mean'),
    total_sold=('rooms_sold', 'sum'),
    total_unsold=('unsold_rooms', 'sum'),
    avg_price=('room_price', 'mean'),
).reset_index()
country_daily['avg_occupancy'] = country_daily['avg_occupancy'].round(4)
country_daily['avg_price_index'] = country_daily['avg_price_index'].round(2)
country_daily['avg_price'] = country_daily['avg_price'].round(0)

with open(os.path.join(OUTPUT_DIR, 'country_daily.json'), 'w', encoding='utf-8') as f:
    json.dump(country_daily.to_dict(orient='records'), f, ensure_ascii=False, indent=2)

print("All data files generated successfully!", flush=True)
print(f"Files in {OUTPUT_DIR}:", flush=True)
for f in os.listdir(OUTPUT_DIR):
    size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
    print(f"  {f}: {size:,} bytes", flush=True)
