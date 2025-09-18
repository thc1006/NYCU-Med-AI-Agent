# LLM Interface Architecture - Modular and Pluggable Design

## LLM Interface Overview

The Taiwan Medical AI Agent implements a modular, pluggable LLM interface architecture that allows seamless integration of various Large Language Model providers while maintaining strict medical safety controls, output validation, and Taiwan-specific localization requirements.

## Core Design Principles

### 1. Provider Agnostic Design
- **Pluggable Interface**: Support for multiple LLM providers (Anthropic, OpenAI, Google, etc.)
- **Standardized API**: Common interface regardless of underlying provider
- **Configuration-Driven**: Provider selection and configuration via environment variables
- **Fallback Support**: Automatic fallback to alternative providers or rule-based responses

### 2. Medical Safety Integration
- **Safety-First Validation**: All LLM outputs validated against medical safety rules
- **Emergency Override**: Rule-based emergency detection takes precedence over LLM responses
- **Non-Diagnostic Constraints**: Prevents LLM from making diagnostic claims
- **Disclaimer Enforcement**: Mandatory medical disclaimers in all responses

### 3. Taiwan Localization
- **Traditional Chinese Output**: Enforced zh-TW language consistency
- **Cultural Context**: Taiwan medical culture and healthcare system awareness
- **Emergency Integration**: Seamless integration with Taiwan emergency protocols (119, 112, etc.)
- **Respectful Language**: Appropriate medical communication style for Taiwan

### 4. Performance and Reliability
- **Async Operations**: Non-blocking LLM API calls
- **Response Caching**: Intelligent caching of similar queries
- **Timeout Handling**: Graceful degradation on LLM service timeouts
- **Error Recovery**: Robust error handling and fallback mechanisms

## LLM Interface Architecture

### 1. Abstract LLM Provider Interface
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"
    MOCK = "mock"

class MedicalSafetyLevel(str, Enum):
    EMERGENCY = "emergency"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class LLMRequest:
    prompt: str
    context: Dict
    max_tokens: int = 500
    temperature: float = 0.3
    safety_level: MedicalSafetyLevel = MedicalSafetyLevel.MEDIUM
    language: str = "zh-TW"
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class LLMResponse:
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int
    processing_time_ms: int
    safety_validated: bool
    confidence_score: float
    metadata: Dict
    timestamp: datetime

@dataclass
class MedicalGuidanceRequest:
    symptom_text: str
    patient_context: Dict
    emergency_keywords: List[str]
    safety_constraints: Dict
    localization_context: Dict

@dataclass
class MedicalGuidanceResponse:
    advice: str
    urgency_level: str
    safety_validated: bool
    disclaimer: str
    next_steps: List[str]
    emergency_contacts: List[str]
    llm_metadata: Dict

class ILLMProvider(ABC):
    """Abstract interface for LLM providers"""

    @abstractmethod
    async def initialize(self, config: Dict) -> bool:
        """Initialize the LLM provider with configuration"""
        pass

    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM"""
        pass

    @abstractmethod
    async def generate_medical_guidance(self, request: MedicalGuidanceRequest) -> MedicalGuidanceResponse:
        """Generate medical guidance with safety validation"""
        pass

    @abstractmethod
    async def validate_response_safety(self, response: str, context: Dict) -> bool:
        """Validate response meets medical safety requirements"""
        pass

    @abstractmethod
    def get_provider_info(self) -> Dict:
        """Get provider information and capabilities"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider health and availability"""
        pass

    @abstractmethod
    async def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for the request"""
        pass
```

### 2. Anthropic Claude Provider Implementation
```python
import anthropic
from typing import Dict, List, Optional
import json
import time

class AnthropicProvider(ILLMProvider):
    def __init__(self):
        self.client: Optional[anthropic.AsyncAnthropic] = None
        self.model_name = "claude-3-sonnet-20240229"
        self.config = {}
        self.safety_validator = MedicalSafetyValidator()
        self.taiwan_localizer = TaiwanLocalizer()

    async def initialize(self, config: Dict) -> bool:
        """Initialize Anthropic client"""
        try:
            api_key = config.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in configuration")

            self.client = anthropic.AsyncAnthropic(api_key=api_key)
            self.model_name = config.get("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
            self.config = config

            # Test connection
            health_ok = await self.health_check()
            return health_ok

        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
            return False

    async def generate_medical_guidance(self, request: MedicalGuidanceRequest) -> MedicalGuidanceResponse:
        """Generate Taiwan-localized medical guidance with safety validation"""

        # Create safety-constrained prompt
        prompt = self._create_medical_prompt(request)

        llm_request = LLMRequest(
            prompt=prompt,
            context=request.patient_context,
            max_tokens=600,
            temperature=0.2,  # Low temperature for medical advice
            safety_level=MedicalSafetyLevel.HIGH,
            language="zh-TW"
        )

        try:
            # Generate LLM response
            llm_response = await self.generate_response(llm_request)

            # Parse and validate medical response
            medical_response = self._parse_medical_response(llm_response.content)

            # Apply safety validation
            safety_validated = await self._validate_medical_safety(
                medical_response,
                request.emergency_keywords,
                request.safety_constraints
            )

            # Apply Taiwan localization
            localized_response = await self._apply_taiwan_localization(
                medical_response,
                request.localization_context
            )

            return MedicalGuidanceResponse(
                advice=localized_response["advice"],
                urgency_level=localized_response["urgency_level"],
                safety_validated=safety_validated,
                disclaimer=localized_response["disclaimer"],
                next_steps=localized_response["next_steps"],
                emergency_contacts=localized_response["emergency_contacts"],
                llm_metadata={
                    "provider": "anthropic",
                    "model": self.model_name,
                    "tokens_used": llm_response.tokens_used,
                    "processing_time": llm_response.processing_time_ms,
                    "confidence": llm_response.confidence_score
                }
            )

        except Exception as e:
            logger.error(f"Error generating medical guidance: {e}")
            # Fallback to rule-based response
            return await self._generate_fallback_response(request)

    def _create_medical_prompt(self, request: MedicalGuidanceRequest) -> str:
        """Create safety-constrained medical prompt"""

        system_prompt = """
你是一個台灣醫療AI助理，專門提供安全、負責任的健康指導。

重要約束條件：
1. 絕對不得進行醫療診斷或提出診斷結論
2. 所有回應必須以繁體中文(zh-TW)輸出
3. 必須包含適當的醫療免責聲明
4. 對於緊急症狀，必須建議立即撥打119或前往急診
5. 建議諮詢合格醫療專業人員
6. 使用尊重、專業的語言

回應格式要求：
{
    "urgency_level": "emergency|urgent|routine|self_care",
    "advice": "主要建議內容",
    "next_steps": ["具體行動步驟"],
    "emergency_contacts": ["相關緊急聯絡方式"],
    "disclaimer": "醫療免責聲明"
}

台灣緊急聯絡號碼：
- 119: 消防救護車
- 112: 行動電話國際緊急號碼
- 110: 警察局
- 113: 婦幼保護專線
"""

        user_prompt = f"""
患者症狀描述：{request.symptom_text}

患者背景：
年齡：{request.patient_context.get('age', '未提供')}
性別：{request.patient_context.get('gender', '未提供')}

請依據台灣醫療環境提供安全、適當的健康指導建議。
"""

        return f"{system_prompt}\n\n{user_prompt}"

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response from Anthropic Claude"""

        start_time = time.time()

        try:
            message = await self.client.messages.create(
                model=self.model_name,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": request.prompt
                    }
                ]
            )

            processing_time = int((time.time() - start_time) * 1000)

            # Extract response content
            content = message.content[0].text if message.content else ""

            # Calculate confidence score (simplified)
            confidence_score = self._calculate_confidence_score(content, request)

            return LLMResponse(
                content=content,
                provider=LLMProvider.ANTHROPIC,
                model=self.model_name,
                tokens_used=message.usage.input_tokens + message.usage.output_tokens,
                processing_time_ms=processing_time,
                safety_validated=False,  # Will be validated separately
                confidence_score=confidence_score,
                metadata={
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens,
                    "stop_reason": message.stop_reason
                },
                timestamp=datetime.utcnow()
            )

        except anthropic.RateLimitError as e:
            logger.warning(f"Anthropic rate limit exceeded: {e}")
            raise LLMProviderError("Rate limit exceeded", "rate_limit")

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMProviderError(f"API error: {e}", "api_error")

        except Exception as e:
            logger.error(f"Unexpected error with Anthropic: {e}")
            raise LLMProviderError(f"Unexpected error: {e}", "unknown_error")

    async def _validate_medical_safety(self,
                                     response: Dict,
                                     emergency_keywords: List[str],
                                     safety_constraints: Dict) -> bool:
        """Validate medical response safety"""

        # Check for prohibited diagnostic language
        prohibited_phrases = [
            "診斷為", "確定是", "一定是", "患有", "得了",
            "病因是", "處方", "劑量", "療程"
        ]

        advice_text = response.get("advice", "")
        for phrase in prohibited_phrases:
            if phrase in advice_text:
                logger.warning(f"Prohibited diagnostic language detected: {phrase}")
                return False

        # Validate emergency response for critical keywords
        for keyword in emergency_keywords:
            if keyword in advice_text and response.get("urgency_level") != "emergency":
                logger.warning(f"Emergency keyword '{keyword}' detected but urgency not set to emergency")
                return False

        # Check disclaimer presence
        disclaimer = response.get("disclaimer", "")
        required_disclaimer_elements = ["不能取代專業醫療", "緊急狀況請撥打119"]
        if not all(element in disclaimer for element in required_disclaimer_elements):
            logger.warning("Incomplete medical disclaimer")
            return False

        return True

    async def _apply_taiwan_localization(self,
                                       response: Dict,
                                       localization_context: Dict) -> Dict:
        """Apply Taiwan-specific localization"""

        localized = response.copy()

        # Ensure Traditional Chinese
        localized["advice"] = self.taiwan_localizer.ensure_traditional_chinese(
            response.get("advice", "")
        )

        # Add Taiwan emergency contacts
        emergency_contacts = response.get("emergency_contacts", [])
        if "119" not in emergency_contacts:
            emergency_contacts.insert(0, "119")
        if "112" not in emergency_contacts:
            emergency_contacts.append("112")
        localized["emergency_contacts"] = emergency_contacts

        # Enhance disclaimer with Taiwan context
        localized["disclaimer"] = self._get_taiwan_medical_disclaimer()

        # Apply respectful language
        localized["advice"] = self.taiwan_localizer.apply_respectful_language(
            localized["advice"]
        )

        return localized

    def _get_taiwan_medical_disclaimer(self) -> str:
        """Get comprehensive Taiwan medical disclaimer"""
        return (
            "本系統僅提供一般健康資訊參考，不能取代專業醫療診斷或治療。"
            "如有醫療需求，請諮詢合格醫療專業人員。"
            "緊急狀況請立即撥打119（消防救護車）或112（國際緊急號碼）。"
            "本資訊符合台灣醫療法規，但不承擔任何醫療責任。"
        )

    async def _generate_fallback_response(self, request: MedicalGuidanceRequest) -> MedicalGuidanceResponse:
        """Generate rule-based fallback response when LLM fails"""

        # Use rule-based emergency detection
        emergency_detected = any(
            keyword in request.symptom_text
            for keyword in request.emergency_keywords
        )

        if emergency_detected:
            return MedicalGuidanceResponse(
                advice="檢測到可能的緊急醫療狀況，請立即撥打119或前往最近的急診室。",
                urgency_level="emergency",
                safety_validated=True,
                disclaimer=self._get_taiwan_medical_disclaimer(),
                next_steps=[
                    "立即撥打119",
                    "前往最近的急診室",
                    "保持冷靜",
                    "準備健保卡和身分證件"
                ],
                emergency_contacts=["119", "112"],
                llm_metadata={
                    "provider": "fallback",
                    "method": "rule_based",
                    "reason": "LLM_unavailable"
                }
            )
        else:
            return MedicalGuidanceResponse(
                advice="建議諮詢合格醫療專業人員以獲得適當的醫療建議。",
                urgency_level="routine",
                safety_validated=True,
                disclaimer=self._get_taiwan_medical_disclaimer(),
                next_steps=[
                    "預約醫師門診",
                    "準備症狀記錄",
                    "攜帶健保卡就醫"
                ],
                emergency_contacts=["119", "112"],
                llm_metadata={
                    "provider": "fallback",
                    "method": "rule_based",
                    "reason": "LLM_unavailable"
                }
            )

    def get_provider_info(self) -> Dict:
        """Get Anthropic provider information"""
        return {
            "name": "Anthropic Claude",
            "provider": "anthropic",
            "model": self.model_name,
            "capabilities": [
                "medical_guidance",
                "traditional_chinese",
                "safety_validation",
                "taiwan_localization"
            ],
            "max_tokens": 4096,
            "languages": ["zh-TW", "en"],
            "safety_features": [
                "constitutional_ai",
                "medical_safety_training",
                "harmful_content_filtering"
            ]
        }

    async def health_check(self) -> bool:
        """Check Anthropic service health"""
        try:
            test_message = await self.client.messages.create(
                model=self.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "健康檢查"}]
            )
            return bool(test_message.content)
        except Exception as e:
            logger.error(f"Anthropic health check failed: {e}")
            return False

    async def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for Anthropic request"""
        # Simplified cost estimation
        estimated_input_tokens = len(request.prompt) // 4  # Rough approximation
        estimated_output_tokens = request.max_tokens

        # Anthropic pricing (approximate, as of 2024)
        input_cost_per_token = 0.000003  # $3/million tokens
        output_cost_per_token = 0.000015  # $15/million tokens

        total_cost = (
            estimated_input_tokens * input_cost_per_token +
            estimated_output_tokens * output_cost_per_token
        )

        return total_cost
```

### 3. LLM Provider Manager
```python
class LLMProviderManager:
    def __init__(self):
        self.providers: Dict[LLMProvider, ILLMProvider] = {}
        self.primary_provider: Optional[LLMProvider] = None
        self.fallback_providers: List[LLMProvider] = []
        self.provider_health: Dict[LLMProvider, bool] = {}
        self.safety_validator = MedicalSafetyValidator()

    async def initialize(self, config: Dict):
        """Initialize all configured LLM providers"""

        # Register available providers
        await self._register_providers()

        # Initialize primary provider
        primary_provider_name = config.get("PRIMARY_LLM_PROVIDER", "anthropic")
        self.primary_provider = LLMProvider(primary_provider_name)

        # Initialize fallback providers
        fallback_config = config.get("FALLBACK_LLM_PROVIDERS", ["mock"])
        self.fallback_providers = [LLMProvider(p) for p in fallback_config]

        # Initialize all providers
        for provider_type, provider in self.providers.items():
            try:
                success = await provider.initialize(config)
                self.provider_health[provider_type] = success
                if success:
                    logger.info(f"Initialized {provider_type} provider successfully")
                else:
                    logger.warning(f"Failed to initialize {provider_type} provider")
            except Exception as e:
                logger.error(f"Error initializing {provider_type}: {e}")
                self.provider_health[provider_type] = False

    async def _register_providers(self):
        """Register all available LLM providers"""
        self.providers = {
            LLMProvider.ANTHROPIC: AnthropicProvider(),
            LLMProvider.OPENAI: OpenAIProvider(),
            LLMProvider.GOOGLE: GoogleProvider(),
            LLMProvider.MOCK: MockLLMProvider(),
            LLMProvider.LOCAL: LocalLLMProvider()
        }

    async def generate_medical_guidance(self,
                                      request: MedicalGuidanceRequest) -> MedicalGuidanceResponse:
        """Generate medical guidance with provider fallback"""

        # Try primary provider first
        if self.primary_provider and self.provider_health.get(self.primary_provider, False):
            try:
                provider = self.providers[self.primary_provider]
                response = await provider.generate_medical_guidance(request)

                # Validate response safety
                if response.safety_validated:
                    return response
                else:
                    logger.warning(f"Safety validation failed for {self.primary_provider}")
            except Exception as e:
                logger.error(f"Primary provider {self.primary_provider} failed: {e}")
                self.provider_health[self.primary_provider] = False

        # Try fallback providers
        for fallback_provider in self.fallback_providers:
            if self.provider_health.get(fallback_provider, False):
                try:
                    provider = self.providers[fallback_provider]
                    response = await provider.generate_medical_guidance(request)

                    if response.safety_validated:
                        logger.info(f"Fallback to {fallback_provider} successful")
                        return response
                except Exception as e:
                    logger.error(f"Fallback provider {fallback_provider} failed: {e}")
                    self.provider_health[fallback_provider] = False

        # Last resort: rule-based response
        logger.warning("All LLM providers failed, using rule-based fallback")
        return await self._generate_rule_based_response(request)

    async def _generate_rule_based_response(self,
                                          request: MedicalGuidanceRequest) -> MedicalGuidanceResponse:
        """Generate rule-based response when all LLM providers fail"""

        # Use Taiwan medical rules engine
        taiwan_rules = TaiwanMedicalRules()
        rule_response = await taiwan_rules.analyze_symptoms(request.symptom_text)

        return MedicalGuidanceResponse(
            advice=rule_response["advice"],
            urgency_level=rule_response["urgency_level"],
            safety_validated=True,
            disclaimer=rule_response["disclaimer"],
            next_steps=rule_response["next_steps"],
            emergency_contacts=["119", "112"],
            llm_metadata={
                "provider": "rule_based",
                "method": "taiwan_medical_rules",
                "reason": "all_llm_providers_failed"
            }
        )

    async def health_check_all_providers(self) -> Dict[LLMProvider, bool]:
        """Check health of all providers"""
        health_results = {}

        for provider_type, provider in self.providers.items():
            try:
                health_ok = await provider.health_check()
                health_results[provider_type] = health_ok
                self.provider_health[provider_type] = health_ok
            except Exception as e:
                logger.error(f"Health check failed for {provider_type}: {e}")
                health_results[provider_type] = False
                self.provider_health[provider_type] = False

        return health_results

    def get_provider_stats(self) -> Dict:
        """Get statistics for all providers"""
        return {
            "primary_provider": self.primary_provider.value if self.primary_provider else None,
            "fallback_providers": [p.value for p in self.fallback_providers],
            "provider_health": {p.value: h for p, h in self.provider_health.items()},
            "available_providers": [p.value for p, h in self.provider_health.items() if h],
            "total_providers": len(self.providers)
        }
```

### 4. Medical Safety Validator
```python
class MedicalSafetyValidator:
    def __init__(self):
        self.prohibited_patterns = self._load_prohibited_patterns()
        self.required_disclaimers = self._load_required_disclaimers()
        self.emergency_keywords = self._load_emergency_keywords()

    def _load_prohibited_patterns(self) -> List[str]:
        """Load patterns that are prohibited in medical responses"""
        return [
            # Diagnostic claims
            r"診斷為.*",
            r"確定是.*",
            r"一定是.*",
            r"患有.*",
            r"得了.*疾病",

            # Treatment prescriptions
            r"建議服用.*藥",
            r"處方.*",
            r"劑量.*",
            r"需要手術",

            # Prognosis claims
            r"會完全康復",
            r"不會有問題",
            r"沒有危險",
            r"預後良好",

            # Dismissive language
            r"只是.*小問題",
            r"不用擔心",
            r"沒什麼大不了"
        ]

    async def validate_medical_response(self,
                                      response: str,
                                      context: Dict) -> Tuple[bool, List[str]]:
        """Validate medical response against safety criteria"""

        violations = []

        # Check for prohibited patterns
        for pattern in self.prohibited_patterns:
            if re.search(pattern, response):
                violations.append(f"Prohibited pattern detected: {pattern}")

        # Check for required medical disclaimer
        if not self._has_valid_disclaimer(response):
            violations.append("Missing or incomplete medical disclaimer")

        # Check emergency keyword handling
        emergency_keywords_in_context = context.get("emergency_keywords", [])
        if emergency_keywords_in_context and not self._has_emergency_guidance(response):
            violations.append("Emergency keywords detected but no emergency guidance provided")

        # Check language appropriateness
        if not self._uses_appropriate_medical_language(response):
            violations.append("Inappropriate medical language detected")

        return len(violations) == 0, violations

    def _has_valid_disclaimer(self, response: str) -> bool:
        """Check if response has valid medical disclaimer"""
        required_elements = [
            "不能取代專業醫療",
            "緊急狀況請撥打119",
            "諮詢合格醫療專業人員"
        ]

        return all(element in response for element in required_elements)

    def _has_emergency_guidance(self, response: str) -> bool:
        """Check if response includes appropriate emergency guidance"""
        emergency_indicators = [
            "立即撥打119",
            "前往急診",
            "緊急醫療",
            "急診室"
        ]

        return any(indicator in response for indicator in emergency_indicators)

    def _uses_appropriate_medical_language(self, response: str) -> bool:
        """Check if response uses appropriate medical language"""
        # Check for respectful language
        respectful_indicators = ["建議", "可能", "請", "您"]
        has_respectful_language = any(indicator in response for indicator in respectful_indicators)

        # Check for overly casual language
        casual_language = ["隨便", "大概", "應該沒事", "別管了"]
        has_casual_language = any(casual in response for casual in casual_language)

        return has_respectful_language and not has_casual_language

    async def sanitize_response(self, response: str) -> str:
        """Sanitize response to ensure medical safety"""

        sanitized = response

        # Replace prohibited diagnostic language
        replacements = {
            "診斷為": "可能與以下情況相關",
            "確定是": "症狀顯示可能",
            "一定是": "建議考慮",
            "患有": "可能存在"
        }

        for prohibited, replacement in replacements.items():
            sanitized = sanitized.replace(prohibited, replacement)

        # Ensure appropriate caution
        if not any(word in sanitized for word in ["建議", "可能", "請"]):
            sanitized = f"建議{sanitized}"

        # Add disclaimer if missing
        if not self._has_valid_disclaimer(sanitized):
            disclaimer = (
                "\n\n本資訊僅供參考，不能取代專業醫療診斷或治療。"
                "如有醫療需求，請諮詢合格醫療專業人員。"
                "緊急狀況請立即撥打119。"
            )
            sanitized += disclaimer

        return sanitized
```

### 5. LLM Response Caching System
```python
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional

class LLMResponseCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 hour default TTL
        self.similarity_threshold = 0.85

    async def get_cached_response(self,
                                request: MedicalGuidanceRequest) -> Optional[MedicalGuidanceResponse]:
        """Get cached response for similar request"""

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Check exact match first
        cached_data = await self.redis.get(f"llm_response:{cache_key}")
        if cached_data:
            return self._deserialize_response(cached_data)

        # Check for similar requests
        similar_response = await self._find_similar_cached_response(request)
        if similar_response:
            return similar_response

        return None

    async def cache_response(self,
                           request: MedicalGuidanceRequest,
                           response: MedicalGuidanceResponse):
        """Cache LLM response"""

        cache_key = self._generate_cache_key(request)
        serialized_response = self._serialize_response(response)

        # Cache with TTL
        await self.redis.setex(
            f"llm_response:{cache_key}",
            self.cache_ttl,
            serialized_response
        )

        # Update similarity index
        await self._update_similarity_index(request, cache_key)

    def _generate_cache_key(self, request: MedicalGuidanceRequest) -> str:
        """Generate unique cache key for request"""

        # Normalize symptom text for consistent caching
        normalized_symptoms = self._normalize_symptom_text(request.symptom_text)

        # Include relevant context
        cache_data = {
            "symptoms": normalized_symptoms,
            "age_group": self._get_age_group(request.patient_context.get("age")),
            "gender": request.patient_context.get("gender", "unknown"),
            "emergency_keywords": sorted(request.emergency_keywords)
        }

        # Generate hash
        cache_string = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(cache_string.encode('utf-8')).hexdigest()[:16]

    def _normalize_symptom_text(self, text: str) -> str:
        """Normalize symptom text for consistent caching"""

        # Remove extra whitespace
        normalized = ' '.join(text.split())

        # Convert to lowercase for comparison
        normalized = normalized.lower()

        # Remove common variations that don't affect medical meaning
        replacements = {
            '很': '', '非常': '', '特別': '', '有點': '',
            '一直': '', '持續': '', '不斷': ''
        }

        for old, new in replacements.items():
            normalized = normalized.replace(old, new)

        return normalized.strip()

    def _get_age_group(self, age: Optional[int]) -> str:
        """Get age group for caching purposes"""
        if age is None:
            return "unknown"
        elif age < 18:
            return "pediatric"
        elif age < 65:
            return "adult"
        else:
            return "elderly"

    async def _find_similar_cached_response(self,
                                          request: MedicalGuidanceRequest) -> Optional[MedicalGuidanceResponse]:
        """Find similar cached response using text similarity"""

        # Get similarity index
        similarity_keys = await self.redis.keys("llm_similarity:*")

        for key in similarity_keys:
            cached_request_data = await self.redis.get(key)
            if cached_request_data:
                cached_request = json.loads(cached_request_data)

                # Calculate similarity
                similarity = self._calculate_text_similarity(
                    request.symptom_text,
                    cached_request.get("symptom_text", "")
                )

                if similarity >= self.similarity_threshold:
                    # Get cached response
                    cache_key = cached_request.get("cache_key")
                    if cache_key:
                        cached_response = await self.redis.get(f"llm_response:{cache_key}")
                        if cached_response:
                            return self._deserialize_response(cached_response)

        return None

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity between two symptom descriptions"""

        # Simple Jaccard similarity for medical terms
        words1 = set(self._normalize_symptom_text(text1).split())
        words2 = set(self._normalize_symptom_text(text2).split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _serialize_response(self, response: MedicalGuidanceResponse) -> str:
        """Serialize response for caching"""
        return json.dumps({
            "advice": response.advice,
            "urgency_level": response.urgency_level,
            "safety_validated": response.safety_validated,
            "disclaimer": response.disclaimer,
            "next_steps": response.next_steps,
            "emergency_contacts": response.emergency_contacts,
            "llm_metadata": response.llm_metadata,
            "cached_at": datetime.utcnow().isoformat()
        }, ensure_ascii=False)

    def _deserialize_response(self, data: str) -> MedicalGuidanceResponse:
        """Deserialize cached response"""
        response_data = json.loads(data)

        return MedicalGuidanceResponse(
            advice=response_data["advice"],
            urgency_level=response_data["urgency_level"],
            safety_validated=response_data["safety_validated"],
            disclaimer=response_data["disclaimer"],
            next_steps=response_data["next_steps"],
            emergency_contacts=response_data["emergency_contacts"],
            llm_metadata={
                **response_data["llm_metadata"],
                "from_cache": True,
                "cached_at": response_data.get("cached_at")
            }
        )
```

This modular LLM interface architecture ensures that the Taiwan Medical AI Agent can flexibly integrate various LLM providers while maintaining strict medical safety standards, Taiwan localization requirements, and robust fallback mechanisms. The design prioritizes safety, reliability, and cultural appropriateness over pure AI capabilities.