import joblib
import json
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


X, y = make_classification(
    n_samples=1000, 
    n_features=10, 
    n_informative=8,
    n_redundant=2,
    n_classes=3,
    random_state=42
)


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)


accuracy = model.score(X_test_scaled, y_test)
print(f"Model accuracy: {accuracy:.2%}")


joblib.dump(model, 'model.pkl')
joblib.dump(scaler, 'scaler.pkl')


feature_names = [f'feature_{i}' for i in range(10)]
with open('columns.json', 'w') as f:
    json.dump(feature_names, f)

print("\n Files saved successfully:")
print("  - model.pkl")
print("  - scaler.pkl")
print("  - columns.json")
print(f"\n Model info:")
print(f"  - Features: {len(feature_names)}")
print(f"  - Classes: {model.classes_.tolist()}")
print(f"  - Accuracy: {accuracy:.2%}")
print("\n Test prediction:")
print(f"  Input shape: (1, 10)")
sample_input = X_test[0].reshape(1, -1)
sample_scaled = scaler.transform(sample_input)
prediction = model.predict(sample_scaled)
probabilities = model.predict_proba(sample_scaled)
print(f"  Prediction: {prediction[0]}")
print(f"  Probabilities: {probabilities[0].round(3)}")