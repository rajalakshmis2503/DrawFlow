import cv2
import mediapipe as mp
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import joblib

# Initialize MediaPipe Hand module
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

# Load the MNIST dataset
digits = load_digits()

# Split the dataset into training and validation sets
X_train, X_valid, y_train, y_valid = train_test_split(digits.data, digits.target, test_size=0.2, random_state=42)

# Initialize an SVM classifier
classifier = SVC()

# Train the classifier on the training data
classifier.fit(X_train, y_train)

# Evaluate the classifier on the validation data
y_pred = classifier.predict(X_valid)
accuracy = accuracy_score(y_valid, y_pred)
print("Validation Accuracy:", accuracy)

# Save the trained classifier for later use
joblib.dump(classifier, 'handwriting_classifier.pkl')
