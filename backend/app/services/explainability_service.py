from typing import Any
import structlog

log = structlog.get_logger()


class ExplainabilityService:
    @staticmethod
    def build_explanation(
        prediction: Any,
        shap_values: dict,
        evidence: list[dict],
        model_type: str,
        confidence: float,
    ) -> dict:
        top_features = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
        feature_explanations = [
            f"'{name}' contributed {val:+.3f} to the prediction"
            for name, val in top_features
        ]
        evidence_summary = []
        for e in evidence[:3]:
            src = e.get("source_name", "unknown source")
            score = e.get("score", 0)
            evidence_summary.append(f"Evidence from {src} (relevance: {score:.2f})")

        return {
            "model_type": model_type,
            "confidence": round(confidence, 4),
            "confidence_label": ExplainabilityService._confidence_label(confidence),
            "top_features": [{"name": k, "impact": round(v, 4)} for k, v in top_features],
            "feature_explanations": feature_explanations,
            "evidence_sources": evidence_summary,
            "evidence_count": len(evidence),
            "narrative": ExplainabilityService._generate_narrative(
                prediction, top_features, confidence, model_type
            ),
        }

    @staticmethod
    def _confidence_label(confidence: float) -> str:
        if confidence >= 0.85:
            return "high"
        if confidence >= 0.65:
            return "medium"
        return "low"

    @staticmethod
    def _generate_narrative(prediction: Any, top_features: list, confidence: float, model_type: str) -> str:
        conf_label = ExplainabilityService._confidence_label(confidence)
        feature_text = ", ".join(f[0] for f in top_features[:3]) if top_features else "the available data"
        return (
            f"The {model_type} model produced this recommendation with {conf_label} confidence "
            f"({confidence:.0%}). The primary drivers were {feature_text}. "
            f"This analysis is based on patterns detected in the historical data and the "
            f"current ontology context. Human review is recommended before taking action."
        )

    @staticmethod
    def build_risk_explanation(risk_score: float, shap_values: dict, category: str) -> str:
        severity = "critical" if risk_score > 0.8 else "high" if risk_score > 0.6 else "medium" if risk_score > 0.4 else "low"
        top = max(shap_values, key=shap_values.get, default="unknown factor")
        return (
            f"Risk score: {risk_score:.2f} ({severity}). "
            f"Category: {category}. "
            f"Primary driver: {top} (impact: {shap_values.get(top, 0):.3f}). "
            f"Immediate attention recommended for {severity} severity risks."
        )
