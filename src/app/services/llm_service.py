# app/services/llm_services.py
import json
import re
import uuid
import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from app.config import settings

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except Exception:
    genai = None


# -----------------------
# Normalizers & JSON utils
# -----------------------
class DataNormalizer:
    """Handles type conversions and small normalizations."""

    @staticmethod
    def parse_gpa(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        if "/" in s:
            try:
                num_s, den_s = s.split("/", 1)
                num = float(re.sub(r"[^\d.+-eE]", "", num_s))
                den = float(re.sub(r"[^\d.+-eE]", "", den_s))
                if den == 0:
                    return None
                if abs(den - 4.0) < 1e-9:
                    return round(num, 3)
                return round((num / den) * 4.0, 3)
            except Exception:
                return None
        if s.endswith("%"):
            try:
                pct = float(s.rstrip("%").strip())
                return round((pct / 100.0) * 4.0, 3)
            except Exception:
                return None
        m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                return None
        return None

    @staticmethod
    def normalize_languages(value: Any) -> List[Dict[str, str]]:
        if not isinstance(value, list):
            return []
        if len(value) == 0:
            return []
        if isinstance(value[0], dict):
            return value
        if isinstance(value[0], str):
            return [{"language": s, "proficiency": ""} for s in value]
        return []

    @staticmethod
    def to_str_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            out = []
            for it in value:
                if isinstance(it, str):
                    out.append(it)
                elif isinstance(it, dict):
                    for k in ("name", "language", "skill", "title", "text"):
                        if k in it and isinstance(it[k], str):
                            out.append(it[k])
                            break
                    else:
                        out.append(json.dumps(it, default=str))
                else:
                    out.append(str(it))
            return out
        if isinstance(value, str):
            return [value]
        return [str(value)]

    @staticmethod
    def to_str(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            if all(isinstance(x, str) for x in value):
                return "\n".join(value)
            return "\n".join([json.dumps(x, default=str) if isinstance(x, dict) else str(x) for x in value])
        if isinstance(value, dict):
            for k in ("explanation", "explain", "text", "content", "recommendation"):
                if k in value and isinstance(value[k], str):
                    return value[k]
            return json.dumps(value, default=str)
        return str(value)

    @staticmethod
    def normalize_score(value: Any) -> int:
        if value is None:
            return 0
        if isinstance(value, int):
            return max(0, min(100, value))
        if isinstance(value, float):
            return max(0, min(100, int(round(value))))
        m = re.search(r"-?\d+", str(value))
        if m:
            try:
                return max(0, min(100, int(m.group(0))))
            except Exception:
                return 0
        return 0


class JSONParser:
    """Robust extraction + JSON parsing helpers."""

    @staticmethod
    def clean_json_string(content: str) -> str:
        if not content:
            return ""
        s = content.strip()
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*```$", "", s, flags=re.IGNORECASE)
        m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s)
        if m:
            return m.group(1)
        return s

    @staticmethod
    def parse_json(json_text: str) -> Dict[str, Any]:
        if not json_text or not json_text.strip():
            return {"_parse_error": "empty json_text", "_raw": json_text}
        try:
            parsed = json.loads(json_text)
            if isinstance(parsed, list):
                return {"_parsed_list": parsed}
            return parsed if isinstance(parsed, dict) else {"result": parsed}
        except json.JSONDecodeError:
            logger.warning("JSONDecodeError, attempting repairs")
        try:
            repaired = json_text.replace("\r\n", "\n").replace("\t", " ")
            repaired = repaired.replace("'", '"')
            repaired = re.sub(r",\s*}", "}", repaired)
            repaired = re.sub(r",\s*]", "]", repaired)
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", repaired)
            if m:
                repaired = m.group(1)
            parsed = json.loads(repaired)
            if isinstance(parsed, list):
                return {"_parsed_list": parsed}
            return parsed if isinstance(parsed, dict) else {"result": parsed}
        except Exception as e:
            logger.exception("Failed to repair JSON: %s", e)
            return {"_raw": json_text, "_parse_error": str(e)}


# -----------------------
# MatchingResult Builder
# -----------------------
class MatchingResultBuilder:
    """
    Centralized builder that normalizes arbitrary LLM outputs / dicts into a safe
    canonical payload and creates the Pydantic model using explicit keyword args.
    """

    CANONICAL_FIELDS = {
        "match_id",
        "resume_id",
        "job_title",
        "scores",
        "matched_skills",
        "missing_skills",
        "strengths",
        "gaps",
        "recommendation",
        "explanation",
    }

    ALIAS_MAP = {
        "matchId": "match_id",
        "match-id": "match_id",
        "resumeId": "resume_id",
        "resume-id": "resume_id",
        "jobTitle": "job_title",
        "job-title": "job_title",
        "matchingResults": "scores",
        "matchedSkills": "matched_skills",
        "matched-skills": "matched_skills",
        "missingSkills": "missing_skills",
        "missing-skills": "missing_skills",
        "strengthAreas": "strengths",
        "strength": "strengths",
        "gapAnalysis": "gaps",
        "gap": "gaps",
        "weaknesses": "gaps",
    }

    @staticmethod
    def _camel_to_snake_safe(key: str) -> str:
        """
        Robust camelCase -> snake_case converter.
        - No-op if key already snake or all-lower.
        """
        if not isinstance(key, str) or not key:
            return key
        if "_" in key or key.islower():
            return key
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", key)
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
        return s2.lower()

    @classmethod
    def _inspect_pydantic_model(cls) -> Dict[str, Any]:
        """Log/return model field alias info (best-effort)."""
        info = {}
        try:
            from app.api.schemas import MatchingResult
            if hasattr(MatchingResult, "model_fields"):
                for fname, finfo in MatchingResult.model_fields.items():
                    alias = getattr(finfo, "alias", None) if finfo is not None else None
                    info[fname] = {"alias": alias, "has_alias": alias is not None and alias != fname}
            elif hasattr(MatchingResult, "__fields__"):
                for fname, finfo in MatchingResult.__fields__.items():
                    alias = getattr(finfo, "alias", None)
                    info[fname] = {"alias": alias, "has_alias": alias is not None and alias != fname}
            logger.debug("Pydantic MatchingResult field info: %s", info)
        except Exception as e:
            logger.debug("Could not inspect Pydantic model: %s", e)
        return info

    @classmethod
    def normalize_keys(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert camelCase keys to snake_case safely, resolve explicit alias map,
        and produce a dict containing only canonical fields with first-wins behavior.
        """
        if not isinstance(data, dict):
            return {}

        # Work on a shallow copy to allow modifications
        src = dict(data)
        # Step 1: convert camelCase -> snake_case (move values, don't duplicate)
        for key in list(src.keys()):
            if isinstance(key, str) and any(c.isupper() for c in key):
                snake = cls._camel_to_snake_safe(key)
                if snake != key:
                    if snake in src:
                        # canonical already present, drop the camel key
                        logger.debug("Dropping camel key '%s' because '%s' exists", key, snake)
                        src.pop(key, None)
                        continue
                    # move value from camel to snake
                    logger.debug("Converting key '%s' -> '%s'", key, snake)
                    src[snake] = src.pop(key)

        # Step 2: apply alias map and keep only canonical fields
        result: Dict[str, Any] = {}
        for key, val in src.items():
            canonical = cls.ALIAS_MAP.get(key, key)
            if canonical in cls.CANONICAL_FIELDS:
                if canonical not in result:
                    result[canonical] = val
                else:
                    logger.debug("Duplicate canonical '%s' found; keeping first value", canonical)

        # Step 3: include any canonical fields that exist in src but were not in alias map
        for cand in cls.CANONICAL_FIELDS:
            if cand not in result and cand in src:
                result[cand] = src[cand]

        return result

    @staticmethod
    def _normalize_scores(scores_obj: Any) -> Dict[str, int]:
        default = {
            "overall_score": 0,
            "skills_match": 0,
            "experience_match": 0,
            "education_match": 0,
        }
        if not scores_obj:
            return default
        normalizer = DataNormalizer()
        if isinstance(scores_obj, dict):
            return {k: normalizer.normalize_score(scores_obj.get(k, 0)) for k in default.keys()}
        text = ""
        if isinstance(scores_obj, list):
            text = " ".join(str(x) for x in scores_obj)
        else:
            text = str(scores_obj)
        nums = re.findall(r"-?\d+", text)
        if nums:
            out = default.copy()
            for i, k in enumerate(default.keys()):
                if i < len(nums):
                    try:
                        out[k] = max(0, min(100, int(nums[i])))
                    except Exception:
                        pass
            return out
        return default

    @classmethod
    def build_safe_payload(
        cls,
        data: Dict[str, Any],
        match_id: Optional[str] = None,
        resume_id: Optional[str] = None,
        job_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return an explicit, canonical payload dict safe for Pydantic construction.
        Coerces match_id to a scalar string and normalizes lists/strings.
        """
        if not isinstance(data, dict):
            data = {}

        # Unwrap _parsed_list if present
        if "_parsed_list" in data and isinstance(data["_parsed_list"], list):
            if data["_parsed_list"]:
                first = data["_parsed_list"][0]
                if isinstance(first, dict):
                    data = first

        clean = cls.normalize_keys(data)

        # match_id precedence and coercion
        if match_id:
            final_match_id = str(match_id)
        elif "match_id" in clean:
            mid = clean["match_id"]
            if isinstance(mid, (list, tuple, set)):
                final_match_id = str(next(iter(mid))) if mid else str(uuid.uuid4())
            elif isinstance(mid, dict):
                final_match_id = str(mid.get("id") or mid.get("match_id") or uuid.uuid4())
            else:
                final_match_id = str(mid) if mid else str(uuid.uuid4())
        else:
            final_match_id = str(uuid.uuid4())

        # resume_id / job_title precedence
        final_resume_id = str(resume_id) if resume_id else str(clean.get("resume_id", ""))
        final_job_title = str(job_title) if job_title else str(clean.get("job_title", ""))

        # normalize scores and list/string fields
        scores_input = clean.get("scores") or clean.get("score") or {}
        normalized_scores = cls._normalize_scores(scores_input)

        normalizer = DataNormalizer()
        final_payload = {
            "match_id": final_match_id,
            "resume_id": final_resume_id,
            "job_title": final_job_title,
            "scores": normalized_scores,
            "matched_skills": normalizer.to_str_list(clean.get("matched_skills", [])),
            "missing_skills": normalizer.to_str_list(clean.get("missing_skills", [])),
            "strengths": normalizer.to_str_list(clean.get("strengths", [])),
            "gaps": normalizer.to_str_list(clean.get("gaps", [])),
            "recommendation": normalizer.to_str(clean.get("recommendation", "")),
            "explanation": normalizer.to_str(clean.get("explanation", "")),
        }

        # sanity log
        if len(final_payload) != len(cls.CANONICAL_FIELDS):
            logger.debug(
                "Final payload field count mismatch: expected %d got %d",
                len(cls.CANONICAL_FIELDS),
                len(final_payload),
            )

        return final_payload

    @classmethod
    def to_pydantic_model(cls, payload: Dict[str, Any]):
        """Safely create a Pydantic MatchingResult instance using explicit args."""
        try:
            from app.api.schemas import MatchingResult, MatchingScore
        except Exception as e:
            logger.exception("Could not import MatchingResult from app.api.schemas: %s", e)
            raise

        logger.debug("Creating MatchingResult model with keys: %s", list(payload.keys()))

        # Inspect model once (best-effort)
        if not hasattr(cls, "_model_inspected"):
            cls._inspect_pydantic_model()
            cls._model_inspected = True

        # Convert scores to MatchingScore if schema expects it
        if "scores" in payload and isinstance(payload["scores"], dict):
            try:
                if hasattr(MatchingScore, "model_validate"):
                    payload["scores"] = MatchingScore.model_validate(payload["scores"])
                else:
                    payload["scores"] = MatchingScore(**payload["scores"])
            except Exception as e:
                logger.warning("Failed to create MatchingScore: %s", e)

        # Explicit keyword instantiation avoids duplicate-kwarg issues
        try:
            model = MatchingResult(
                match_id=payload["match_id"],
                resume_id=payload["resume_id"],
                job_title=payload["job_title"],
                scores=payload["scores"],
                matched_skills=payload["matched_skills"],
                missing_skills=payload["missing_skills"],
                strengths=payload["strengths"],
                gaps=payload["gaps"],
                recommendation=payload["recommendation"],
                explanation=payload["explanation"],
            )
            return model
        except TypeError as te:
            # If we still get TypeError, log diagnostics fully
            logger.error("TypeError while creating MatchingResult: %s", te)
            logger.error("Payload (truncated): %s", json.dumps(payload, default=str)[:2000])
            logger.error("Payload keys: %s", list(payload.keys()))
            raise
        except Exception as e:
            logger.exception("Failed to create MatchingResult model: %s", e)
            logger.error("Payload: %s", json.dumps(payload, default=str, indent=2))
            raise


# -----------------------
# LLMService core
# -----------------------
class LLMService:
    """Gemini (google.generativeai) integration for structured resume parsing."""

    def __init__(self):
        google_key = getattr(settings, "GOOGLE_API_KEY", None)
        if not google_key:
            logger.warning("GOOGLE_API_KEY not set in settings")
        if genai is None:
            raise RuntimeError("google.generativeai package not available; pip install google-generativeai")
        try:
            genai.configure(api_key=google_key or "")
        except Exception as e:
            logger.exception("Failed to configure google.generativeai: %s", e)
        self.model = getattr(settings, "GEMINI_MODEL", "models/gemini-2.5-flash")
        self.parser = JSONParser()
        self.normalizer = DataNormalizer()
        self.result_builder = MatchingResultBuilder()

    async def _call_gemini(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.0) -> Any:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        def sync_call():
            model = genai.GenerativeModel(self.model)
            methods = [
                (lambda: genai.generate_text(model=self.model, prompt=prompt, max_output_tokens=max_tokens, temperature=temperature)) if hasattr(genai, "generate_text") else None,
                lambda: model.generate_content(prompt, max_output_tokens=max_tokens),
                lambda: model.generate_content(prompt),
                lambda: model.generate_content({"content": {"parts": [{"text": prompt}]}, "max_output_tokens": max_tokens}),
                lambda: model.generate_content({"parts": [{"text": prompt}], "max_output_tokens": max_tokens}),
            ]
            for method in methods:
                if method is None:
                    continue
                try:
                    res = method()
                    if res is not None:
                        return res
                except Exception as e:
                    logger.debug("genai method failed: %s", e)
                    continue
            raise RuntimeError("No compatible generate_content/generate_text method succeeded for this google.generativeai version.")
        return await loop.run_in_executor(None, sync_call)

    def _extract_text_from_response(self, raw_resp: Any) -> str:
        if raw_resp is None:
            return ""
        for attr in ("text", "output", "output_text"):
            try:
                val = getattr(raw_resp, attr, None)
                if val:
                    return str(val)
            except Exception:
                continue
        try:
            cands = getattr(raw_resp, "candidates", None)
            if cands and len(cands) > 0:
                first = cands[0]
                for attr in ("content", "output", "text"):
                    val = getattr(first, attr, None)
                    if val:
                        return str(val)
                if isinstance(first, dict):
                    for k in ("content", "output", "text"):
                        if k in first and first[k]:
                            return str(first[k])
        except Exception:
            pass
        if isinstance(raw_resp, dict):
            for k in ("output", "text", "response", "candidates"):
                if k in raw_resp and raw_resp[k]:
                    return str(raw_resp[k])
        try:
            return json.dumps(raw_resp, default=str)
        except Exception:
            return str(raw_resp)

    def _normalize_resume_data(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(parsed, dict):
            return parsed
        # education gpa normalization
        educ = parsed.get("education")
        if isinstance(educ, list):
            for i, e in enumerate(educ):
                if isinstance(e, dict) and "gpa" in e:
                    gpa_val = self.normalizer.parse_gpa(e["gpa"])
                    if gpa_val is not None:
                        parsed["education"][i]["gpa"] = gpa_val
                    else:
                        parsed["education"][i]["_gpa_parse_error"] = e["gpa"]
        # languages normalization
        skills = parsed.get("skills")
        if isinstance(skills, dict):
            langs = skills.get("languages")
            if isinstance(langs, list):
                parsed["skills"]["languages"] = self.normalizer.normalize_languages(langs)
        return parsed

    async def extract_structured_data(self, text: str, prompt: str = "") -> Dict[str, Any]:
        system_msg = (
            "You are an expert resume parser. OUTPUT JSON ONLY. "
            "Do NOT include explanations or extra text.\n\n"
            "Return a single JSON object with the exact schema shown below. "
            "All keys must appear; if a value is unknown, use null."
        )
        schema = {
            "id": "string or null",
            "file_name": "string or null",
            "personal_info": {
                "full_name": "string or null",
                "first_name": "string or null",
                "last_name": "string or null",
                "email": "string or null",
                "phone": "string or null",
                "address": "string or null",
                "linkedin": "string or null",
                "website": "string or null",
            },
            "summary": "string or null",
            "experience": [
                {
                    "title": "string",
                    "company": "string",
                    "location": "string or null",
                    "start_date": "string or null",
                    "end_date": "string or null",
                    "description": "string or null",
                    "technologies": ["string"],
                }
            ],
            "education": [
                {
                    "degree": "string",
                    "institution": "string",
                    "start_date": "string or null",
                    "end_date": "string or null",
                    "gpa": "string or null",
                    "details": "string or null",
                }
            ],
            "skills": {"technical": ["string"], "soft": ["string"], "languages": ["string"]},
            "certifications": [
                {"name": "string", "issuer": "string or null", "issued": "string or null", "expires": "string or null"}
            ],
            "raw_text": "string",
            "processed_at": "string (ISO8601) or null",
        }
        full_prompt = f"{system_msg}\n\nJSON SCHEMA:\n{json.dumps(schema, indent=2)}\n\nNOW PARSE THE FOLLOWING RESUME TEXT:\n{text}\n\nReturn ONLY valid JSON matching the schema."
        if prompt:
            full_prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{prompt}"
        try:
            raw_resp = await self._call_gemini(full_prompt, max_tokens=3200, temperature=0.0)
            content = self._extract_text_from_response(raw_resp)
            logger.info("LLM response length: %d chars", len(content))
            json_str = self.parser.clean_json_string(content)
            parsed = self.parser.parse_json(json_str)
            parsed = self._normalize_resume_data(parsed)
            if "_raw" in parsed or "_parse_error" in parsed:
                parsed["_original_model_text"] = content
            return parsed
        except Exception as e:
            logger.exception("extract_structured_data failed: %s", e)
            return {"error": str(e)}

    async def analyze_match(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            "You are an expert job-matching assistant. Analyze the resume against "
            "the job description and return a SINGLE JSON OBJECT with these keys:\n\n"
            "{\n"
            '  "match_id": "string",\n'
            '  "resume_id": "string",\n'
            '  "job_title": "string",\n'
            '  "scores": {\n'
            '    "overall_score": 0-100,\n'
            '    "skills_match": 0-100,\n'
            '    "experience_match": 0-100,\n'
            '    "education_match": 0-100\n'
            '  },\n'
            '  "matched_skills": ["skill1", "skill2"],\n'
            '  "missing_skills": ["skill3", "skill4"],\n'
            '  "strengths": ["strength1", "strength2"],\n'
            '  "gaps": ["gap1", "gap2"],\n'
            '  "recommendation": "string",\n'
            '  "explanation": "string"\n'
            "}\n\n"
            f"Resume Data:\n{json.dumps(resume_data)}\n\n"
            f"Job Description:\n{json.dumps(job_data)}\n\n"
            "Return ONLY the JSON object. No additional text."
        )
        try:
            raw_parsed = await self.extract_structured_data("", prompt)
            safe_payload = self.result_builder.build_safe_payload(
                raw_parsed, resume_id=resume_data.get("id", ""), job_title=job_data.get("title", "")
            )
            return safe_payload
        except Exception as e:
            logger.exception("analyze_match failed: %s", e)
            return {
                "match_id": str(uuid.uuid4()),
                "resume_id": resume_data.get("id", ""),
                "job_title": job_data.get("title", ""),
                "scores": {"overall_score": 0, "skills_match": 0, "experience_match": 0, "education_match": 0},
                "matched_skills": [],
                "missing_skills": [],
                "strengths": [],
                "gaps": [],
                "recommendation": "",
                "explanation": f"Analysis error: {str(e)}",
            }

    def make_matching_result(
        self,
        data: Dict[str, Any],
        match_id: Optional[str] = None,
        resume_id: Optional[str] = None,
        job_title: Optional[str] = None,
        as_model: bool = False,
    ) -> Union[Dict[str, Any], Any]:
        """
        Create a MatchingResult dict or Pydantic model.
        Use explicit instantiation when as_model True to avoid duplicate-key issues.
        """
        safe_payload = MatchingResultBuilder.build_safe_payload(
            data, match_id=match_id, resume_id=resume_id, job_title=job_title
        )
        if not as_model:
            return safe_payload
        try:
            return MatchingResultBuilder.to_pydantic_model(safe_payload)
        except Exception as e:
            logger.exception("Failed to create Pydantic model: %s", e)
            return safe_payload


# -----------------------
# Convenience factory (permanent fix helper)
# -----------------------
def create_matching_result_from_raw(
    data: Dict[str, Any],
    match_id: Optional[str] = None,
    resume_id: Optional[str] = None,
    job_title: Optional[str] = None,
):
    """
    One-line factory that normalizes arbitrary raw dicts and returns a Pydantic MatchingResult
    created via explicit keyword args (no dict-unpack).
    Usage: from app.services.llm_services import create_matching_result_from_raw
    """
    safe = MatchingResultBuilder.build_safe_payload(data, match_id=match_id, resume_id=resume_id, job_title=job_title)
    try:
        from app.api.schemas import MatchingResult  # type: ignore
    except Exception as e:
        logger.exception("Could not import MatchingResult model: %s", e)
        raise
    return MatchingResult(
        match_id=safe["match_id"],
        resume_id=safe["resume_id"],
        job_title=safe["job_title"],
        scores=safe["scores"],
        matched_skills=safe["matched_skills"],
        missing_skills=safe["missing_skills"],
        strengths=safe["strengths"],
        gaps=safe["gaps"],
        recommendation=safe["recommendation"],
        explanation=safe["explanation"],
    )
