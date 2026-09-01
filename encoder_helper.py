from sklearn.preprocessing import LabelEncoder
import pandas as pd

class RobustLabelEncoder:
    """Label encoder wrapper that handles unseen classes gracefully."""
    def __init__(self):
        self.encoder = LabelEncoder()
        self.classes_ = []

    def fit(self, series):
        unique_vals = list(series.unique())
        if '<unknown>' not in unique_vals:
            unique_vals.append('<unknown>')
        self.encoder.fit(unique_vals)
        self.classes_ = self.encoder.classes_
        return self

    def transform(self, series):
        # Map values not in classes_ to '<unknown>'
        safe_series = series.apply(lambda x: x if x in self.classes_ else '<unknown>')
        return self.encoder.transform(safe_series)

    def inverse_transform(self, encoded):
        return self.encoder.inverse_transform(encoded)
