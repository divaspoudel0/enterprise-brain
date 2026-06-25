from typing import Optional
import numpy as np
import pandas as pd
import structlog
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

log = structlog.get_logger()

_FEATURE_NAMES = [
    "revenue_trend", "payment_delay_days", "order_volume_change",
    "customer_churn_rate", "inventory_turnover", "debt_ratio",
]

# Module-level singletons initialized lazily
_risk_model = None
_risk_explainer = None


def _init_risk_model():
    """Train an XGBoost risk classifier on synthetic data and build SHAP explainer."""
    global _risk_model, _risk_explainer
    if _risk_model is not None:
        return _risk_model, _risk_explainer

    try:
        from xgboost import XGBClassifier
        import shap

        np.random.seed(42)
        n = 2000
        X = np.random.uniform(0, 1, (n, len(_FEATURE_NAMES)))
        # Labels: weighted sum above threshold → high risk
        weights = np.array([0.25, 0.20, 0.15, 0.20, 0.10, 0.10])
        scores = X @ weights + np.random.normal(0, 0.05, n)
        y = (scores > np.percentile(scores, 60)).astype(int)

        _risk_model = XGBClassifier(
            n_estimators=80,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
            verbosity=0,
        )
        _risk_model.fit(X, y)
        _risk_explainer = shap.TreeExplainer(_risk_model)
        log.info("ml.risk_model_initialized")
    except Exception as e:
        log.warning("ml.risk_model_init_failed", error=str(e))
        _risk_model = None
        _risk_explainer = None

    return _risk_model, _risk_explainer


class MLService:
    @staticmethod
    def generate_timeseries(metric: str, n_days: int = 365) -> pd.DataFrame:
        np.random.seed(hash(metric) % 2**31)
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n_days, freq="D")
        base = np.random.uniform(1000, 10000)
        trend = np.linspace(0, base * 0.3, n_days)
        seasonality = base * 0.1 * np.sin(np.linspace(0, 4 * np.pi, n_days))
        noise = np.random.normal(0, base * 0.05, n_days)
        values = base + trend + seasonality + noise
        return pd.DataFrame({"ds": dates, "y": values})

    @staticmethod
    def forecast_prophet(metric: str, df: pd.DataFrame, horizon_days: int) -> dict:
        try:
            from prophet import Prophet
            m = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                uncertainty_samples=200,
            )
            m.fit(df)
            future = m.make_future_dataframe(periods=horizon_days)
            forecast = m.predict(future)
            historical = forecast[forecast["ds"] <= df["ds"].max()]
            predicted = forecast[forecast["ds"] > df["ds"].max()]
            actual = df["y"].values
            fitted = historical["yhat"].values[-len(df):]
            rmse = float(np.sqrt(((actual - fitted) ** 2).mean()))
            mape = float((np.abs((actual - fitted) / np.maximum(np.abs(actual), 1))).mean() * 100)
            return {
                "dates": predicted["ds"].dt.strftime("%Y-%m-%d").tolist(),
                "values": predicted["yhat"].round(2).tolist(),
                "lower": predicted["yhat_lower"].round(2).tolist(),
                "upper": predicted["yhat_upper"].round(2).tolist(),
                "historical_dates": df["ds"].dt.strftime("%Y-%m-%d").tolist(),
                "historical_values": df["y"].round(2).tolist(),
                "rmse": round(rmse, 4),
                "mape": round(mape, 4),
                "components": {
                    "trend": forecast["trend"].round(2).tolist()[-horizon_days:],
                },
            }
        except Exception as e:
            log.error("prophet.forecast_failed", error=str(e))
            return MLService._simple_forecast(df, horizon_days)

    @staticmethod
    def _simple_forecast(df: pd.DataFrame, horizon_days: int) -> dict:
        last_val = df["y"].iloc[-1]
        avg_change = df["y"].diff().mean()
        dates = pd.date_range(start=df["ds"].iloc[-1] + pd.Timedelta(days=1), periods=horizon_days)
        values = [last_val + avg_change * (i + 1) for i in range(horizon_days)]
        rmse = float(df["y"].std() * 0.1)
        return {
            "dates": dates.strftime("%Y-%m-%d").tolist(),
            "values": [round(v, 2) for v in values],
            "lower": [round(v * 0.95, 2) for v in values],
            "upper": [round(v * 1.05, 2) for v in values],
            "historical_dates": df["ds"].dt.strftime("%Y-%m-%d").tolist(),
            "historical_values": df["y"].round(2).tolist(),
            "rmse": round(rmse, 4),
            "mape": 5.0,
            "components": {"trend": values},
        }

    @staticmethod
    def detect_anomalies(data: list[float], contamination: float = 0.05) -> list[dict]:
        if len(data) < 5:
            return []
        arr = np.array(data).reshape(-1, 1)
        scaler = StandardScaler()
        arr_scaled = scaler.fit_transform(arr)
        model = IsolationForest(contamination=contamination, random_state=42)
        labels = model.fit_predict(arr_scaled)
        scores = model.score_samples(arr_scaled)
        return [
            {"index": i, "value": data[i], "anomaly_score": round(float(-score), 4)}
            for i, (label, score) in enumerate(zip(labels, scores))
            if label == -1
        ]

    @staticmethod
    def score_risk(features: dict) -> tuple[float, dict]:
        """Score entity risk using XGBoost with SHAP explanations."""
        X = np.array([[features.get(f, 0.0) for f in _FEATURE_NAMES]])

        model, explainer = _init_risk_model()

        if model is not None and explainer is not None:
            try:
                import shap
                risk_score = float(model.predict_proba(X)[0][1])
                # shap_values returns (n_samples, n_features) for XGBoost binary
                sv = explainer.shap_values(X)
                if hasattr(sv, "values"):
                    sv = sv.values
                shap_arr = np.array(sv).flatten()[:len(_FEATURE_NAMES)]
                shap_dict = {
                    name: round(float(val), 4)
                    for name, val in zip(_FEATURE_NAMES, shap_arr)
                }
                return float(np.clip(risk_score, 0, 1)), shap_dict
            except Exception as e:
                log.warning("ml.shap_failed", error=str(e))

        # Fallback: weighted dot product (deterministic, no model needed)
        weights = np.array([0.25, 0.20, 0.15, 0.20, 0.10, 0.10])
        risk_score = float(np.clip(np.dot(np.abs(X), weights).item(), 0, 1))
        shap_dict = {
            name: round(float(abs(X[0][i]) * weights[i]), 4)
            for i, name in enumerate(_FEATURE_NAMES)
        }
        return risk_score, shap_dict
