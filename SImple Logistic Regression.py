import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_breast_cancer
from sklearn.metrics import accuracy_score, confusion_matrix

breast_cancer = load_breast_cancer()

X = breast_cancer.data
y = breast_cancer.target
print(f"total features used: {X.shape[1]}")
print(f"total samples: {X.shape[0]}")

# Split the data, 80% for training and 20% for testing
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.4, random_state=42
)
print(f"training samples: {len(X_train)}")

model = LogisticRegression( max_iter=5000)
model.fit(X_train, y_train)
print("model trained successfully")
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)
print(f"**Classification Accuracy Score: {accuracy:.4f}**")
print("\nConfusion Matrix:")
print(conf_matrix)

plt.figure(figsize=(10, 6)) 
plt.scatter(
    y_test,
    y_pred,
    color = "red",
    alpha = 0.5,
    label = "Predicted vs Actual"
)


# Plot the regression line
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--', lw=2, label='Perfect Fit line')

plt.xlabel('Malignant Score (0)')
plt.ylabel('Benign Score (1)')
plt.title('Malignant vs Benign Scores (Multivariate Model)')
plt.legend()
plt.grid(True)
plt.show() 
