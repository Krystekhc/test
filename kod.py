from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import zscore
from fpdf import FPDF
import tempfile

pytrends = TrendReq(hl='en-US', tz=120, timeout=(20, 60), proxies={}, retries=3, backoff_factor=0.8)

# Lista słów kluczowych do analizy
kw_list = ["wojna", "wybuch", "atak"]

# Polska w ciągu ostatnich 12 miesięcy
pytrends.build_payload(kw_list, cat=0, timeframe='today 12-m', geo='PL', gprop='')

# Zainteresowanie w czasie
data = pytrends.interest_over_time()

# Nie ruszać, w dokumentacji kazali korzystać
if 'isPartial' in data.columns:
    data = data.drop(columns=['isPartial'])

# Oblicz znormalizowane wartości Z-score dla wykrywania anomalii
data_zscore = data.apply(zscore)

# Próg do określenia anomalii, dodatni = powyżej średniej
anomaly_threshold = 2

# Stwórz maskę wykrywającą anomalie
anomalies = (data_zscore.abs() > anomaly_threshold)

# Wyświetl pierwsze kilka wierszy danych w konsoli
print(data.head())
print("\nWykryte anomalie:")
print(anomalies)

# Wykres liniowy z anomaliami
plt.figure(figsize=(14, 7))
sns.lineplot(data=data)

# Nanieś wykryte anomalie na wykres jako czerwone kropki
for keyword in kw_list:
    plt.scatter(
        data.index[anomalies[keyword]],
        data[keyword][anomalies[keyword]],
        color='red',
        s=100,
        label=f"Anomalie ({keyword})"
    )

# Dodaj tytuł, etykiety osi oraz legendę
plt.title("Popularność wyszukiwań w Google Trends wraz z wykrytymi anomaliami")
plt.ylabel("Popularność")
plt.xlabel("Data")
plt.xticks(rotation=45)
plt.legend(loc='upper left')
plt.grid(True)

# Zapisywanie wykresu do tymczasowego pliku
temp_image = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
plt.savefig(temp_image.name)

# Lista anomali jako tekst
anomaly_texts = []
for keyword in kw_list:
    detected_dates = data.index[anomalies[keyword]].strftime("%Y-%m-%d").tolist()
    if detected_dates:
        anomaly_texts.append(f"Anomalie dla {keyword}: {', '.join(detected_dates)}")
    else:
        anomaly_texts.append(f"Brak wykrytych anomalii dla {keyword}.")

# Utwórz dokument PDF
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# Dodaj tytuł raportu
pdf.set_font("Arial", "B", 16)
pdf.cell(0, 10, "Raport Google Trends - Anomalie", ln=True, align='C')
pdf.ln(10)

# Dodaj opis wykresu
pdf.set_font("Arial", "", 12)
pdf.multi_cell(0, 10, "\n".join(anomaly_texts))
pdf.ln(10)

# Dodaj obraz wykresu do raportu
pdf.image(temp_image.name, x=10, w=180)

# Zapisz raport do pliku PDF
pdf_file = "raport_google_trends.pdf"
pdf.output(pdf_file)

temp_image.close()
print(f"Raport został zapisany jako {pdf_file}.")

plt.show()
