import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.preprocessing import LabelEncoder
import joblib
import io

# --- Data Loading ---
try:
    filepath = r"C:\Users\MSI\Downloads\archive (2)\Combined Data.csv"
    df = pd.read_csv(filepath)
    print(df.head())
except Exception as e:
    print(f"Error loading file: {e}")

# --- Data Preprocessing ---
print("Missing values before handling:")
print(df[['statement', 'status']].isnull().sum())

df.dropna(subset=['statement'], inplace=True)

print("\nMissing values after handling:")
print(df[['statement', 'status']].isnull().sum())

if df['status'].isnull().sum() > 0:
    df.dropna(subset=['status'], inplace=True)
    print("Missing values in status handled by dropping.")

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text

df['statement_cleaned'] = df['statement'].apply(clean_text)

# Encode the 'status' column
label_encoder = LabelEncoder()
df['status_encoded'] = label_encoder.fit_transform(df['status'])

print("\nData preprocessing complete.")

# --- Text Vectorization ---
tfidf_vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_tfidf = tfidf_vectorizer.fit_transform(df['statement_cleaned'])
y = df['status_encoded']

print(f"\nShape of TF-IDF matrix: {X_tfidf.shape}")

# --- Model Training ---
X_train_tfidf, X_test_tfidf, y_train, y_test = train_test_split(X_tfidf, y, test_size=0.2, random_state=42)
lsvc_model = LinearSVC(random_state=42, max_iter=1000)
lsvc_model.fit(X_train_tfidf, y_train)
print("\nModel training complete (LinearSVC).")

# --- Save Model, Vectorizer and LabelEncoder ---
try:
    joblib.dump(lsvc_model, "mental_health_model.pkl")
    joblib.dump(tfidf_vectorizer, "vectorizer.pkl")
    joblib.dump(label_encoder, "label_encoder.pkl")  # <-- SAVING LABEL ENCODER
    
    print("\nModel, vectorizer and label encoder saved successfully!")
except Exception as e:
    print(f"\nError saving model/vectorizer/label encoder: {e}")

# --- Prediction Function ---
def predict_mental_health(text, model, vectorizer, label_encoder):
    cleaned_text = clean_text(text)
    text_vector = vectorizer.transform([cleaned_text])
    predicted_encoded_status = model.predict(text_vector)
    predicted_status = label_encoder.inverse_transform(predicted_encoded_status)
    return predicted_status[0]

# --- Interactive Testing ---
while True:
    user_input = input("\nEntrez un texte pour prédire l'état mental (ou 'quit' pour quitter) : ")
    if user_input.lower() == 'quit':
        print("Fin du test.")
        break
    prediction = predict_mental_health(user_input, lsvc_model, tfidf_vectorizer, label_encoder)
    print(f"Prédiction : {prediction}")
