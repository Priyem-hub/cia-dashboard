"""
conflict_model.py
-----------------
Machine learning model for predicting geopolitical conflict risk scores.
Uses scikit-learn with a Random Forest Regressor trained on conflict indicators.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings("ignore")


# ── Feature definitions ──────────────────────────────────────────────────────

FEATURE_COLUMNS = [
    "military_spending",   # % of GDP spent on military (0–25)
    "sanctions",           # sanction intensity index (0–10)
    "trade_dependency",    # trade openness / dependency index (0–10)
    "diplomatic_stability" # diplomatic relations stability score (0–10)
]

TARGET_COLUMN = "risk_score"   # 0–100 conflict risk


# ── Synthetic training data augmentation ─────────────────────────────────────

def _generate_synthetic_samples(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic training samples to supplement the small CSV dataset.
    Rules encode domain knowledge about how each factor drives conflict risk.
    """
    rng = np.random.default_rng(seed)

    mil  = rng.uniform(0, 25, n)        # military_spending
    sanc = rng.uniform(0, 10, n)        # sanctions
    trade= rng.uniform(0, 10, n)        # trade_dependency (higher = safer)
    dip  = rng.uniform(0, 10, n)        # diplomatic_stability (higher = safer)

    # Domain-encoded risk formula
    raw_risk = (
        2.8  * mil            # heavy militarisation raises risk
      + 4.5  * sanc           # sanctions strongly correlate with conflict
      - 3.0  * trade          # trade integration lowers risk
      - 5.5  * dip            # stable diplomacy strongly lowers risk
      + rng.normal(0, 5, n)   # noise
      + 20                    # baseline
    )

    risk = np.clip(raw_risk, 0, 100)

    return pd.DataFrame({
        "military_spending":   mil,
        "sanctions":           sanc,
        "trade_dependency":    trade,
        "diplomatic_stability":dip,
        "risk_score":          risk,
    })


# ── Model class ───────────────────────────────────────────────────────────────

class ConflictRiskModel:
    """
    Ensemble conflict-risk predictor.

    Attributes
    ----------
    model : sklearn Pipeline
        Trained [scaler → GradientBoostingRegressor] pipeline.
    is_trained : bool
    metrics : dict  – MAE and R² on the held-out test set.
    feature_importances : dict
    """

    def __init__(self):
        self.model: Pipeline | None = None
        self.is_trained: bool = False
        self.metrics: dict = {}
        self.feature_importances: dict = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def train(self, csv_path: str = "dataset.csv") -> dict:
        """
        Load CSV, augment with synthetic data, train model, return metrics.
        """
        # 1. Load real data
        df_real = pd.read_csv(csv_path)
        df_real = df_real[FEATURE_COLUMNS + [TARGET_COLUMN]].dropna()

        # 2. Augment with synthetic samples
        df_synth = _generate_synthetic_samples(n=600)
        df = pd.concat([df_real, df_synth], ignore_index=True)

        X = df[FEATURE_COLUMNS].values
        y = df[TARGET_COLUMN].values

        # 3. Train / test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 4. Build pipeline
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("gbr", GradientBoostingRegressor(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.08,
                subsample=0.85,
                random_state=42,
            )),
        ])
        self.model.fit(X_train, y_train)

        # 5. Evaluate
        y_pred = self.model.predict(X_test)
        self.metrics = {
            "mae":  round(float(mean_absolute_error(y_test, y_pred)), 2),
            "r2":   round(float(r2_score(y_test, y_pred)), 4),
            "samples_trained": len(X_train),
        }

        # 6. Feature importances (from inner GBR)
        gbr = self.model.named_steps["gbr"]
        importances = gbr.feature_importances_
        self.feature_importances = {
            feat: round(float(imp), 4)
            for feat, imp in zip(FEATURE_COLUMNS, importances)
        }

        self.is_trained = True
        return self.metrics

    def predict(
        self,
        military_spending: float,
        sanctions: float,
        trade_dependency: float,
        diplomatic_stability: float,
    ) -> dict:
        """
        Predict conflict risk for a single scenario.

        Parameters
        ----------
        military_spending     : 0–25  (% of GDP)
        sanctions             : 0–10
        trade_dependency      : 0–10
        diplomatic_stability  : 0–10

        Returns
        -------
        dict with keys: risk_score, risk_level, confidence_band, contributing_factors
        """
        if not self.is_trained:
            self.train()

        features = np.array([[
            military_spending,
            sanctions,
            trade_dependency,
            diplomatic_stability,
        ]])

        score = float(np.clip(self.model.predict(features)[0], 0, 100))

        # Confidence band via individual tree predictions
        gbr = self.model.named_steps["gbr"]
        scaler = self.model.named_steps["scaler"]
        X_scaled = scaler.transform(features)

        # Simulate uncertainty with staged predictions
        stage_preds = np.array([
            est.predict(X_scaled)[0]
            for est in gbr.estimators_[:, 0]   # each stage's tree
        ])
        cumulative = np.cumsum(gbr.learning_rate * stage_preds) + gbr.init_.predict(X_scaled)[0]
        std = float(np.std(cumulative[-50:]))   # std of last 50 stages ≈ convergence noise
        confidence_band = (
            round(max(0, score - 1.96 * std), 1),
            round(min(100, score + 1.96 * std), 1),
        )

        # Classify risk level
        if score >= 80:
            level = "CRITICAL"
            level_color = "#FF0000"
        elif score >= 65:
            level = "HIGH"
            level_color = "#FF4500"
        elif score >= 45:
            level = "ELEVATED"
            level_color = "#FF8C00"
        elif score >= 25:
            level = "MODERATE"
            level_color = "#FFD700"
        else:
            level = "LOW"
            level_color = "#32CD32"

        # Per-factor contribution (normalised SHAP-lite)
        raw_contributions = {
            "Military Spending":    military_spending  * self.feature_importances.get("military_spending", 0.25),
            "Sanctions":            sanctions           * self.feature_importances.get("sanctions", 0.30),
            "Trade Dependency":     (10 - trade_dependency) * self.feature_importances.get("trade_dependency", 0.20),
            "Diplomatic Stability": (10 - diplomatic_stability) * self.feature_importances.get("diplomatic_stability", 0.25),
        }
        total = sum(raw_contributions.values()) or 1
        contributing_factors = {
            k: round(v / total * 100, 1)
            for k, v in raw_contributions.items()
        }

        return {
            "risk_score":           round(score, 1),
            "risk_level":           level,
            "risk_level_color":     level_color,
            "confidence_band":      confidence_band,
            "contributing_factors": contributing_factors,
        }

    def batch_predict(self, df: pd.DataFrame) -> pd.Series:
        """
        Predict risk scores for a DataFrame containing FEATURE_COLUMNS.
        Missing columns are filled with neutral defaults.
        """
        if not self.is_trained:
            self.train()

        defaults = {
            "military_spending": 2.0,
            "sanctions": 3.0,
            "trade_dependency": 5.0,
            "diplomatic_stability": 5.0,
        }
        X = df.reindex(columns=FEATURE_COLUMNS).fillna(defaults).values
        preds = np.clip(self.model.predict(X), 0, 100)
        return pd.Series(preds.round(1), index=df.index, name="predicted_risk")


# ── Module-level singleton ────────────────────────────────────────────────────

_model_instance: ConflictRiskModel | None = None


def get_model(csv_path: str = "dataset.csv") -> ConflictRiskModel:
    """Return a trained singleton model (lazy-init)."""
    global _model_instance
    if _model_instance is None or not _model_instance.is_trained:
        _model_instance = ConflictRiskModel()
        _model_instance.train(csv_path)
    return _model_instance


# ── CLI quick-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Training conflict risk model …")
    m = ConflictRiskModel()
    metrics = m.train()
    print(f"\n✓ Model trained  |  MAE={metrics['mae']}  R²={metrics['r2']}")
    print(f"  Feature importances: {m.feature_importances}")

    scenarios = [
        ("High-risk state",   18.0, 9.0, 2.0, 1.0),
        ("Moderate tension",   4.5, 5.0, 5.5, 4.5),
        ("Stable democracy",   1.8, 0.0, 8.2, 8.5),
    ]
    print("\n── Scenario predictions ──────────────────────────────────────────")
    for name, mil, sanc, trade, dip in scenarios:
        result = m.predict(mil, sanc, trade, dip)
        print(
            f"  {name:<22}  score={result['risk_score']:>5.1f}  "
            f"level={result['risk_level']:<10}  "
            f"CI={result['confidence_band']}"
        )
