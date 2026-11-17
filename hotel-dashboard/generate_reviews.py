"""
Generate AI External Reviews & Fake Review Filter Dataset for the 165 hotels.
Includes:
- Multi-platform simulated reviews (Google Maps, Booking.com, Agoda, TripAdvisor)
- Sentiment analysis (Cleanliness, Service, Facilities, Dining, Value for Money)
- Fake Review Detection flags (Account anomaly, Semantic unnatural, Fact contradiction, Time cluster)
- Quality rating (3-star High, 2-star Medium, 1-star Low, Filtered Fake)
- Correlation cross-analysis with occupancy, room price, facility score
"""
import json
import random
import os

OUTPUT_DIR = r'C:\Users\HTL22\Downloads\grafana-main41211232\hotel-dashboard\data'
PUBLIC_DIR = r'C:\Users\HTL22\Downloads\grafana-main41211232\hotel-dashboard\public\data'

with open(os.path.join(OUTPUT_DIR, 'hotel_directory.json'), encoding='utf-8') as f:
    hotels = json.load(f)

random.seed(41211232)

platforms = ['Google Maps', 'Booking.com', 'Agoda', 'TripAdvisor']
aspects = ['清潔度', '服務態度', '設施品質', '餐飲品質', '性價比']

# Templates for good and bad reviews per aspect
templates = {
    '清潔度': {
        'pos': ['房間非常乾淨，浴室一塵不染，床單散發淡淡清香。', '打掃得很徹底，角落完全沒有灰塵，衛生要求極高。', '整體整潔度讓人非常安心，備品整齊乾淨。'],
        'neg': ['地毯有明顯污漬與異味，讓人不太舒服。', '浴室磁磚邊緣有發霉痕跡，清潔需要加強。', '床單感覺有些潮濕，房內有微弱霉味。']
    },
    '服務態度': {
        'pos': ['櫃台接待親切主動，入住手續迅速且詳細介紹設施。', '員工服務非常貼心，主動協助搬運行李並推薦在地美食。', '服務人員態度誠懇親切，有賓至如歸的感覺。'],
        'neg': ['櫃台服務態度冷漠，詢問問題顯得不耐煩。', '入住手續處理緩慢，排隊等候超過半小時。', '電話客服響了很久才接，處理要求速度拖延。']
    },
    '設施品質': {
        'pos': ['硬體設施新穎現代化，健身房與泳池維護得非常好。', '房間隔音極佳，空調安靜舒適，床鋪支撐力很好。', '公共設施高級大器，高空景觀令人驚艷。'],
        'neg': ['設備較為老舊，冷氣運轉聲較大影響睡眠。', '插座數量較少且位置不便，電視連線訊號不穩。', '泳池水質維護普通，部分健身器材有故障待修。']
    },
    '餐飲品質': {
        'pos': ['早餐菜色豐富多樣，現煮熱食與現做烘焙水準極高。', '飯店餐廳料理精緻美味，食材新鮮且兼具在地特色。', '自助吧補菜迅速，咖啡與甜點品質出乎意料的好。'],
        'neg': ['早餐選擇偏少且菜色偏冷，口味普通。', '餐飲定價過高但品質普通，CP值不高。', '尖峰時段取餐動線壅塞，補餐速度有些落後。']
    },
    '性價比': {
        'pos': ['以這個價位能享受到這種品質，絕對物超所值！', '促銷方案非常划算，整體體驗超出預期。', '性價比極高，下次造訪一定會再次選擇入住。'],
        'neg': ['每晚房價偏高，但服務與設施並未達到相應水準。', '整體感覺定價過高，性價比略顯不足。', '額外收費項目多，整體花費比預期高出不少。']
    }
}

fake_templates = [
    {'reason': '語意不自然 / 機器生成', 'text': '這是一家無與倫比極致奢華至高享受的偉大飯店五顆星好評！'},
    {'reason': '帳號行為異常 / 短期刷評', 'text': '超棒超好很喜歡推薦大家一定要來！'},
    {'reason': '內容與事實矛盾', 'text': '頂樓無邊際海景泳池太棒了！（但本館為市中心商務館且無海景泳池）'},
    {'reason': '競業惡意刷負評', 'text': '千萬別住這家，爛到不行，建議大家都去住隔壁那家！'},
    {'reason': '時間群聚異常', 'text': '普通普通普通，完全不值一顧，快點避雷！'}
]

all_reviews = []
hotel_review_stats = []

for h in hotels:
    hname = h['hotel_name']
    country = h['country']
    city = h['city']
    occ = h['avg_occupancy']
    price_idx = h['avg_price_index']
    fac = h['facility_score']
    
    # Positive sentiment probability influenced by facility score and occupancy
    pos_prob = min(0.92, max(0.45, 0.4 + (fac / 10.0) * 0.3 + (occ - 0.5) * 0.4))
    
    hotel_revs = []
    # Generate 15-25 reviews per hotel
    num_revs = random.randint(15, 25)
    
    aspect_scores = {asp: {'pos': 0, 'neg': 0} for asp in aspects}
    fake_count = 0
    cred_counts = {'3-star': 0, '2-star': 0, '1-star': 0, 'filtered': 0}
    
    for i in range(num_revs):
        platform = random.choice(platforms)
        is_fake = random.random() < 0.18  # 18% chance of fake review
        date_day = random.randint(1, 31)
        date_str = f"2026-10-{date_day:02d}"
        
        if is_fake:
            fake_item = random.choice(fake_templates)
            rev = {
                'id': f"R_{h['hotel_id']}_{i+1:02d}",
                'hotel_name': hname,
                'country': country,
                'city': city,
                'platform': platform,
                'date': date_str,
                'is_fake': True,
                'filter_reason': fake_item['reason'],
                'credibility': '❌ 已過濾虛假評論',
                'credibility_score': 0,
                'sentiment': '異常/過濾',
                'aspect': '異常檢測',
                'content': fake_item['text'],
                'user': f"User_{random.randint(1000, 9999)}"
            }
            fake_count += 1
            cred_counts['filtered'] += 1
        else:
            aspect = random.choice(aspects)
            is_pos = random.random() < pos_prob
            sentiment = '好評' if is_pos else '負評'
            aspect_scores[aspect]['pos' if is_pos else 'neg'] += 1
            
            # Credibility distribution
            cred_roll = random.random()
            if cred_roll < 0.45:
                cred = '⭐⭐⭐ 高可信度'
                cred_score = 3
                cred_counts['3-star'] += 1
            elif cred_roll < 0.8:
                cred = '⭐⭐ 中可信度'
                cred_score = 2
                cred_counts['2-star'] += 1
            else:
                cred = '⭐ 低可信度'
                cred_score = 1
                cred_counts['1-star'] += 1
                
            rev_text = random.choice(templates[aspect]['pos' if is_pos else 'neg'])
            rev = {
                'id': f"R_{h['hotel_id']}_{i+1:02d}",
                'hotel_name': hname,
                'country': country,
                'city': city,
                'platform': platform,
                'date': date_str,
                'is_fake': False,
                'filter_reason': '通過真實性驗證',
                'credibility': cred,
                'credibility_score': cred_score,
                'sentiment': sentiment,
                'aspect': aspect,
                'content': rev_text,
                'user': f"Guest_{random.randint(10000, 99999)}"
            }
        hotel_revs.append(rev)
        all_reviews.append(rev)
        
    real_revs = [r for r in hotel_revs if not r['is_fake']]
    real_pos = sum(1 for r in real_revs if r['sentiment'] == '好評')
    real_neg = sum(1 for r in real_revs if r['sentiment'] == '負評')
    pos_rate = round(real_pos / len(real_revs), 4) if real_revs else 0
    
    hotel_review_stats.append({
        'hotel_name': hname,
        'hotel_id': h['hotel_id'],
        'country': country,
        'city': city,
        'total_reviews': num_revs,
        'real_reviews': len(real_revs),
        'fake_reviews': fake_count,
        'fake_rate': round(fake_count / num_revs, 4),
        'real_pos': real_pos,
        'real_neg': real_neg,
        'pos_rate': pos_rate,
        'aspect_scores': aspect_scores,
        'cred_counts': cred_counts,
        # Operational indicators for cross-comparison
        'avg_occupancy': occ,
        'avg_price_index': price_idx,
        'facility_score': fac,
        'total_rooms': h['total_rooms'],
        'size_group': h['size_group']
    })

# Summary KPIs
total_reviews = len(all_reviews)
total_real = sum(1 for r in all_reviews if not r['is_fake'])
total_fake = sum(1 for r in all_reviews if r['is_fake'])
total_pos = sum(1 for r in all_reviews if r['sentiment'] == '好評')
total_neg = sum(1 for r in all_reviews if r['sentiment'] == '負評')

# Platform distribution
platform_stats = {}
for p in platforms:
    p_revs = [r for r in all_reviews if r['platform'] == p]
    platform_stats[p] = {
        'total': len(p_revs),
        'real': sum(1 for r in p_revs if not r['is_fake']),
        'fake': sum(1 for r in p_revs if r['is_fake']),
        'fake_rate': round(sum(1 for r in p_revs if r['is_fake']) / len(p_revs), 4)
    }

# Aspect total stats
aspect_total = {}
for a in aspects:
    a_revs = [r for r in all_reviews if r.get('aspect') == a]
    a_pos = sum(1 for r in a_revs if r['sentiment'] == '好評')
    a_neg = sum(1 for r in a_revs if r['sentiment'] == '負評')
    aspect_total[a] = {
        'total': len(a_revs),
        'pos': a_pos,
        'neg': a_neg,
        'pos_rate': round(a_pos / len(a_revs), 4) if a_revs else 0
    }

# Fake reasons distribution
fake_reasons = {}
for r in all_reviews:
    if r['is_fake']:
        reason = r['filter_reason']
        fake_reasons[reason] = fake_reasons.get(reason, 0) + 1

output_payload = {
    'summary': {
        'total_reviews': total_reviews,
        'total_real': total_real,
        'total_fake': total_fake,
        'fake_rate': round(total_fake / total_reviews, 4),
        'total_pos': total_pos,
        'total_neg': total_neg,
        'overall_pos_rate': round(total_pos / total_real, 4),
        'platforms_count': len(platforms),
        'hotels_covered': len(hotels)
    },
    'platforms': platform_stats,
    'aspects': aspect_total,
    'fake_reasons': fake_reasons,
    'hotel_stats': hotel_review_stats,
    'sample_reviews': all_reviews[:300]  # First 300 reviews for interactive UI display
}

with open(os.path.join(OUTPUT_DIR, 'reviews_analysis.json'), 'w', encoding='utf-8') as f:
    json.dump(output_payload, f, ensure_ascii=False, indent=2)

with open(os.path.join(PUBLIC_DIR, 'reviews_analysis.json'), 'w', encoding='utf-8') as f:
    json.dump(output_payload, f, ensure_ascii=False, indent=2)

print(f"Reviews dataset generated successfully! Total: {total_reviews}, Real: {total_real}, Fake: {total_fake}")
