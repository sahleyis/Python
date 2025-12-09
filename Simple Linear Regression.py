# all the libraries and imports im gonna need
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_diabetes
from sklearn.metrics import mean_squared_error, r2_score

# loading the data set
diabetes = load_diabetes()

#select only the BMI input, x is the input and y is the output
x = diabetes.data # i can do this to allow it to access all 442 rows and 10 columns, giving it all the information it needs
y = diabetes.target
print(f"total features used: {x.shape[1]}") # shape[1] gives the number of columns/features
print(f"total samples: {x.shape[0]}")  # shape[0] gives the number of rows/samples
print("data loaded successfully")

#split the datat, 80% for training and 20% for testing
X_train, X_test, y_train, y_test = train_test_split(
    x, y, test_size=0.4, random_state=42
)
print(f"training samples: {len(X_train)}")
print(f"testing samples: {len(X_test)}")

# the linear regression model
model = LinearRegression()

# train the model (teaching the computer the relationship between X_train and y_train)
model.fit(X_train, y_train)
print("model trained successfully")

# ask it to make predictions 
y_pred = model.predict(X_test)

# what line did the model find? (y = mx + b)
print("\n--MODEL PARAMETERS--")
# co efficent (m or slope)
print(f"Coefficient (10 features): {model.coef_}")
#intercept (b)
print(f"Intercept: {model.intercept_}")

# 3. Evaluation Metrics (How good is the fit?)
print("\n--- Evaluation Metrics ---") # the /n is jst saying to make a new line

# Mean Squared Error (MSE): A measure of the average error, or how far off the line is from the actual data points. Lower is better.
print(f"Mean Squared Error (MSE): {mean_squared_error(y_test, y_pred):.2f}")

# R-squared Score (R²): The most important score. It tells you the percentage of the variation in the output (Y) that the input (X) can explain.
# Example: R² of 0.30 means 30% of disease progression is explained by BMI. Closer to 1.0 is better
final_r2_Score = r2_score(y_test, y_pred)
print(f"R-squared Score (R²): {final_r2_Score:.2f}")


# Plot the actual test data points (scatter plot)
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

plt.xlabel('Actual Disease Progression Score    ')
plt.ylabel('Predicted Disease Progression Score')
plt.title('Actual vs. Predicted Scores (Multivariate Model')
plt.legend()
plt.grid(True)
plt.show() 
