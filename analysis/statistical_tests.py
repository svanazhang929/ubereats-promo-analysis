import duckdb
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
import warnings
warnings.filterwarnings('ignore')

DB_PATH = "data/ubereats.duckdb"
con = duckdb.connect(DB_PATH)

# 从silver层拿个体数据
df = con.execute("SELECT * FROM main_silver.silver_restaurants").fetchdf()
print(f"Total records: {len(df)}")
print(f"With rating: {df['rating'].notna().sum()}")
print(f"With promo: {df['has_promo'].sum()}")
print()

# 只保留有评分的
df = df[df['rating'].notna()].copy()

# ── H1: 有促销 vs 无促销，评分是否有显著差异 ──
promo = df[df['has_promo']==1]['rating']
no_promo = df[df['has_promo']==0]['rating']

t_stat, p_value = stats.ttest_ind(promo, no_promo)
print("═══ H1: Promo vs No Promo — Rating ═══")
print(f"  No Promo:  n={len(no_promo)}, mean={no_promo.mean():.3f}, std={no_promo.std():.3f}")
print(f"  Has Promo: n={len(promo)}, mean={promo.mean():.3f}, std={promo.std():.3f}")
print(f"  t-stat={t_stat:.3f}, p-value={p_value:.4f}")
print(f"  Result: {'SIGNIFICANT (p<0.05)' if p_value < 0.05 else 'NOT significant (p>=0.05)'}")
print()

# ── H2: 有促销 vs 无促销，评论数是否有显著差异 ──
promo_rev = df[df['has_promo']==1]['review_count_num'].dropna()
no_promo_rev = df[df['has_promo']==0]['review_count_num'].dropna()

t_stat2, p_value2 = stats.ttest_ind(promo_rev, no_promo_rev)
print("═══ H2: Promo vs No Promo — Review Count ═══")
print(f"  No Promo:  n={len(no_promo_rev)}, mean={no_promo_rev.mean():.0f}")
print(f"  Has Promo: n={len(promo_rev)}, mean={promo_rev.mean():.0f}")
print(f"  t-stat={t_stat2:.3f}, p-value={p_value2:.4f}")
print(f"  Result: {'SIGNIFICANT (p<0.05)' if p_value2 < 0.05 else 'NOT significant (p>=0.05)'}")
print()

# ── H3: 评分较低的餐厅是否更倾向于跑促销 ──
print("═══ H3: Do lower-rated restaurants run more promos? ═══")
avg_by_promo = df.groupby('has_promo')['rating'].mean()
print(f"  Avg rating — No Promo: {avg_by_promo[0]:.3f}")
print(f"  Avg rating — Has Promo: {avg_by_promo[1]:.3f}")
direction = "lower" if avg_by_promo[1] < avg_by_promo[0] else "higher"
print(f"  Promo restaurants have {direction} avg ratings — H3 {'SUPPORTED' if direction=='lower' else 'NOT supported'}")
print()

# ── 回归：控制suburb和delivery_fee后，促销对评分的net effect ──
df_reg = df[['rating', 'has_promo', 'suburb', 'delivery_fee']].dropna()
model = smf.ols('rating ~ has_promo + C(suburb) + delivery_fee', data=df_reg).fit()
print("═══ Regression: Effect of promo on rating (controlling for suburb + delivery_fee) ═══")
print(f"  R-squared: {model.rsquared:.3f}")
print(f"  has_promo coef: {model.params['has_promo']:.4f}")
print(f"  has_promo p-value: {model.pvalues['has_promo']:.4f}")
print(f"  Result: {'SIGNIFICANT' if model.pvalues['has_promo'] < 0.05 else 'NOT significant'}")
print()

# ── 各促销类型的平均评分对比 ──
print("═══ Avg Rating by Promo Type ═══")
summary = df.groupby('promo_type').agg(
    count=('rating', 'count'),
    avg_rating=('rating', 'mean'),
    avg_reviews=('review_count_num', 'mean')
).round(3)
print(summary.to_string())

con.close()