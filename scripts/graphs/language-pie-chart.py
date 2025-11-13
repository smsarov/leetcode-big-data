import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

df = pd.read_csv('../../results/popular_languages.csv')


df = df.sort_values('user_count', ascending=False)
total = df['user_count'].sum()

df['percentage'] = (df['user_count'] / total * 100)

main_languages = df[df['percentage'] >= 1.5]
other_languages = df[df['percentage'] < 1.5]

if not other_languages.empty:
    other_total = other_languages['user_count'].sum()
    other_percentage = other_languages['percentage'].sum()

    other_row = pd.DataFrame({
        'languagename': ['Другие'],
        'user_count': [other_total],
        'percentage': [other_percentage]
    })

    plot_df = pd.concat([main_languages, other_row])
else:
    plot_df = df

plt.style.use('default')
fig, ax = plt.subplots(figsize=(16, 9))

colors = [
    '#264653', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51',
    '#287271', '#3A506B', '#4A6FA5', '#5D8A76', '#C97B84',
    '#6D6875', '#B5838D', '#E5989B', '#FFB4A2', '#FFCDB2'
]

wedges, texts = ax.pie(
    plot_df['user_count'],
    labels=[f"{lang}\n({pct:.1f}%)" for lang, pct in zip(plot_df['languagename'], plot_df['percentage'])],
    colors=colors[:len(plot_df)],
    startangle=90,
    wedgeprops={'edgecolor': 'white', 'linewidth': 3, 'alpha': 0.85},
    textprops={'fontsize': 9, 'color': 'darkblue', 'fontweight': 'bold'}
)

for text in texts:
    text.set_fontsize(8)
    text.set_color('#2C3E50')
    text.set_fontweight('bold')

ax.set_title('Распределение языков программирования\nпо популярности среди пользователей',
             fontsize=16, fontweight='bold', color='#2C3E50', pad=20)


legend_elements = []
for i, (lang, count, pct) in enumerate(zip(plot_df['languagename'],
                                           plot_df['user_count'],
                                           plot_df['percentage'])):
    if lang != 'Другие':
        legend_elements.append(f"{lang}: {count:,} ({pct:.1f}%)")
ax.legend(legend_elements, title="Основные языки",
          loc="upper left", bbox_to_anchor=(1, 0.5, 0.5, 0.4),
          frameon=True, fancybox=True, shadow=True, fontsize=10)

if not other_languages.empty:
    other_info = [
        f"Другие языки: {other_total:,} ({other_percentage:.1f}%)",
        ""
    ]

    for _, row in other_languages.iterrows():
        other_info.append(f"  {row['languagename']}: {row['user_count']:,} ({row['percentage']:.1f}%)")
    other_text = '\n'.join(other_info)
    ax.text(1.01, 0.3, other_text,
            transform=ax.transAxes, fontsize=10,
            verticalalignment='center',
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8))

centre_circle = plt.Circle((0, 0), 0.50, fc='white', edgecolor='gray', linewidth=2)
ax.add_artist(centre_circle)
ax.text(0, 0, f"Всего пользователей:\n{total:,}",
        ha='center', va='center', fontsize=12, fontweight='bold', color='#2C3E50')
ax.axis('equal')
plt.tight_layout()
plt.savefig('language_popularity_detailed.png', dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.show()