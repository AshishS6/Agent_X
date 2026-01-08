"""
Content Analyzer Module
Handles content risk detection and analysis.
Per PRD V2.1.1: Rule-based keyword matching (non-semantic), each risk must include evidence.
"""

import re
from typing import Dict, List, Optional
from urllib.parse import urlparse


class ContentAnalyzer:
    """Analyzes page content for risks and quality issues"""
    
    # Lorem ipsum patterns
    LOREM_PATTERNS = [
        r'lorem\s+ipsum\s+dolor\s+sit\s+amet',
        r'consectetur\s+adipiscing',
        r'sed\s+do\s+eiusmod'
    ]
    
    # Prohibitive/restrictive phrase patterns for intent classification
    # These patterns indicate the keyword is being mentioned in a prohibitive context
    # (e.g., "we do not allow gambling" vs "try our gambling platform")
    # V2.2: Expanded patterns to catch payment gateway terms, merchant agreements
    PROHIBITIVE_PATTERNS = [
        r'(?:we\s+)?(?:do\s+)?not\s+(?:allow|permit|accept|support|process|offer|provide|sell|deal\s+in)',
        r'(?:is\s+)?(?:strictly\s+)?prohibit(?:ed|s)?',
        r'(?:is\s+)?(?:not\s+)?permitted',
        r'(?:you\s+)?(?:shall|may|must)\s+not',
        r'restriction(?:s)?\s+(?:on|apply|include)',
        r'exclud(?:ed?|ing|es?)\s+(?:from|categories?|items?|products?|services?)',
        r'(?:will\s+)?(?:be\s+)?(?:immediately\s+)?terminat(?:ed?|ion)',
        r'(?:is|are)\s+(?:not\s+)?(?:allowed|permitted|accepted)',
        r'cannot\s+(?:be\s+)?(?:used|processed|accepted)',
        r'ineligible\s+(?:for|to)',
        r'(?:these?\s+)?(?:types?\s+of\s+)?(?:businesses?|merchants?|activities?)\s+(?:are\s+)?(?:not\s+)?(?:allowed|permitted|accepted|supported)',
        r'decline(?:d|s)?\s+(?:to\s+)?(?:process|accept|support)',
        r'reserved?\s+(?:the\s+)?right\s+to\s+(?:refuse|reject|decline|terminate)',
        # V2.2: Additional patterns for payment gateway/merchant agreement language
        r'(?:prohibited|restricted)\s+(?:business(?:es)?|categor(?:y|ies)|activit(?:y|ies)|merchant(?:s)?)',
        r'(?:high[\-\s]?risk|restricted)\s+(?:MCC|merchant\s+category)',
        r'(?:not\s+)?eligible\s+(?:for|to\s+use)',
        r'violat(?:e|es|ing|ion)\s+(?:of\s+)?(?:our|these|the)\s+(?:terms|policies)',
        r'(?:subject\s+to\s+)?(?:additional\s+)?(?:review|scrutiny|approval)',
        r'(?:we\s+)?(?:may\s+)?(?:refuse|reject|decline)\s+(?:to\s+)?(?:process|accept|onboard)',
        r'(?:list\s+of\s+)?(?:prohibited|restricted|banned)\s+(?:goods|products|services|items)',
        r'(?:the\s+)?following\s+(?:are|is)\s+(?:not\s+)?(?:permitted|allowed)',
        r'(?:illegal|unlawful)\s+(?:under|in)\s+(?:any|applicable)\s+(?:law|jurisdiction)',
    ]
    
    # Policy page types where prohibitive intent is expected
    # V2.2.1: Expanded list to include ALL pages that commonly contain boilerplate/legal text
    POLICY_PAGE_TYPES = [
        'privacy_policy', 'terms_conditions', 'terms_condition', 
        'refund_policy', 'returns_refund', 'acceptable_use',
        'prohibited_activities', 'restricted_businesses',
        'shipping_delivery', 'shipping_policy', 'delivery_policy',
        'faq', 'help', 'support', 'legal', 'disclaimer',
        'cancellation_policy', 'cookie_policy', 'data_safety',
        # V2.2.1: Additional page types that often embed payment gateway terms
        'checkout', 'cart', 'payment', 'terms', 'conditions',
        'about', 'legal_hub', 'footer', 'sitemap',
    ]
    
    # V2.2.1: Boilerplate detection patterns
    # If these patterns appear near a keyword, it's likely embedded payment gateway text
    BOILERPLATE_PATTERNS = [
        r'payment\s+(?:gateway|processor|provider|partner|terms)',
        r'(?:razorpay|stripe|paypal|paytm|phonepe|cashfree|payu)\s+(?:terms|policy|guidelines)',
        r'(?:merchant|seller|vendor)\s+(?:agreement|terms|policy|guidelines)',
        r'(?:list\s+of\s+)?(?:prohibited|restricted)\s+(?:business(?:es)?|merchant(?:s)?|activit(?:y|ies)|categor(?:y|ies))',
        r'following\s+(?:types?\s+of\s+)?(?:businesses?|merchants?|activities?|goods?|services?)\s+(?:are|is)\s+(?:not\s+)?(?:permitted|allowed|supported)',
        r'(?:reserve(?:s|d)?|retain(?:s)?)\s+(?:the\s+)?right\s+to\s+(?:refuse|reject|terminate)',
        r'accordance\s+with\s+(?:applicable|local|international)\s+(?:laws?|regulations?)',
        r'compliance\s+with\s+(?:rbi|sebi|fema|pci[\-\s]?dss)',
        r'subject\s+to\s+(?:our|the|these)\s+(?:terms|policies|guidelines)',
    ]
    
    # Restricted keywords by category
    RESTRICTED_KEYWORDS = {
        "gambling": [
            "casino", "betting", "poker", "lottery", "gambling", "sports-betting",
            "online-casino", "bingo", "slot-machine", "blackjack", "roulette",
            "wager", "gambling-site", "online-betting", "jackpot", "slots",
            "card-games", "live-casino", "betting-odds", "gamble"
        ],
        "adult": [
            "adult", "porn", "xxx", "nsfw", "adult-content", "adult-entertainment",
            "erotic", "sex", "pornography", "adult-site", "explicit", "nude",
            "adult-video", "webcam", "fetish", "adult-services", "mature-content",
            "x-rated", "adult-chat", "erotic-content"
        ],
        "crypto": [
            "bitcoin", "crypto", "blockchain", "ico", "token", "cryptocurrency",
            "nft", "ethereum", "altcoin", "wallet", "crypto-exchange",
            "digital-currency", "defi", "staking", "crypto-trading", "coin",
            "decentralized", "smart-contract", "crypto-wallet", "token-sale"
        ],
        "forex": [
            "forex", "fx", "currency-trading", "forex-trading", "currency-exchange",
            "forex-market", "trading-platform", "forex-broker", "currency-pair",
            "pip", "leverage", "forex-signals", "foreign-exchange", "fx-trading",
            "forex-investment", "currency-market", "forex-analysis",
            "trading-account", "forex-strategy", "exchange-rate"
        ],
        "binary": [
            "binary-options", "binary-trading", "binary-betting",
            "binary-investment", "binary-broker", "options-trading",
            "binary-signals", "binary-platform", "binary-market",
            "digital-options", "binary-trade", "binary-strategy",
            "binary-account", "options-investment", "binary-forecast",
            "binary-profit", "binary-exchange", "trading-options",
            "binary-system", "binary-payout"
        ],
        "weapons": [
            "gun", "weapon", "firearm", "ammunition", "explosive", "explosives",
            "bomb", "rifle", "pistol", "shotgun", "bullet", "grenade", "knife",
            "tactical-gear", "arms", "weaponry", "gun-shop", "military-equipment",
            "ammo", "assault-rifle", "brass knuckles", "gun parts", "gun powder"
        ],
        "pharmacy": [
            "viagra", "cialis", "prescription drugs", "online pharmacy",
            "prescription medication", "herbal drugs", "pharmacy online"
        ],
        "alcohol": [
            "alcohol", "alcoholic beverages", "beer", "liquor", "wine", "champagne",
            "whiskey", "vodka", "rum", "alcoholic", "spirits", "alcohol sales"
        ],
        "tobacco": [
            "cigarettes", "cigars", "tobacco", "chewing tobacco", "vape", "e-cigarettes",
            "e-cigs", "vaping", "cigarette store", "tobacco products", "smoking"
        ],
        "drugs": [
            "illegal drugs", "drug paraphernalia", "marijuana", "salvia", "magic mushrooms",
            "cocaine", "heroin", "methamphetamine", "drug accessories", "herbal drugs",
            "drug test circumvention", "drug cleansing", "urine test", "drug test aid"
        ],
        "counterfeit": [
            "counterfeit", "replica", "fake", "imitation", "designer knockoff",
            "unauthorized goods", "fake autograph", "counterfeit stamp", "fake designer"
        ],
        "copyright": [
            "copyright unlocking", "mod chip", "pirated", "unauthorized copy",
            "copyrighted media", "copyrighted software", "cable descrambler",
            "black box", "circumvent copyright", "pirated software", "pirated media"
        ],
        "hacking": [
            "hacking", "cracking", "illegal access", "malware", "hacking materials",
            "cracking materials", "unauthorized access", "hack software", "crack software",
            "bypass security", "hacking tools"
        ],
        "child_pornography": [
            "child porn", "child pornography", "minor", "underage", "child abuse",
            "underage content", "minor pornography"
        ],
        "government_ids": [
            "fake id", "fake passport", "fake diploma", "fake document",
            "government id", "fake license", "noble title", "fake certificate"
        ],
        "body_parts": [
            "body parts", "organs", "organ sale", "body part sale", "organ transplant sale"
        ],
        "endangered_species": [
            "endangered species", "ivory", "rhino horn", "endangered animal",
            "endangered plant", "wildlife trade", "illegal wildlife"
        ],
        "pyrotechnics": [
            "fireworks", "pyrotechnic", "explosive device", "toxic materials",
            "flammable materials", "radioactive materials", "hazardous materials"
        ],
        "regulated_goods": [
            "air bag", "mercury battery", "freon", "pesticide", "surveillance equipment",
            "lock-picking device", "police badge", "government uniform", "slot machine",
            "postage meter", "recalled items"
        ],
        "securities": [
            "stocks", "bonds", "securities", "investment products", "stock trading",
            "bond trading", "securities trading"
        ],
        "traffic_devices": [
            "radar detector", "radar jammer", "license plate cover", "traffic signal changer",
            "speed detector", "traffic device"
        ],
        "wholesale_currency": [
            "discounted currency", "currency exchange", "wholesale currency",
            "currency discount", "bulk currency"
        ],
        "live_animals": [
            "live animals", "animal hides", "animal skins", "animal parts",
            "animal teeth", "animal nails", "wildlife sale"
        ],
        "mlm": [
            "multi-level marketing", "mlm", "pyramid scheme", "matrix scheme",
            "pyramid marketing", "get rich quick", "mlm scheme"
        ],
        "work_at_home": [
            "work at home", "work-at-home", "work from home scheme", "home based business scam"
        ],
        "drop_shipped": [
            "drop ship", "drop-shipped", "dropshipped merchandise", "drop shipping"
        ],
        "money_transfer": [
            "wire transfer", "money transfer", "quasi-cash", "western union",
            "money remittance", "cash disbursement", "account funding"
        ],
        "dating_escort": [
            "dating service", "escort service", "friend finder", "escort",
            "prostitution", "dating site", "escort agency"
        ],
        "massage_parlors": [
            "massage parlor", "massage parlour", "massage service"
        ],
        "detective_agencies": [
            "detective agency", "private investigator", "detective service", "pi service"
        ],
        "political": [
            "political organization", "political party", "political fundraising"
        ],
        "bpo_kpo": [
            "bpo", "kpo", "outsourcing service", "business process outsourcing",
            "knowledge process outsourcing"
        ],
        "job_services": [
            "job service", "employment service", "job placement", "recruitment service"
        ],
        "real_estate": [
            "real estate service", "construction service", "real estate construction"
        ],
        "web_telephony": [
            "calling card", "web telephony", "sms service", "text service",
            "facsimile service", "voice process service", "bandwidth service"
        ],
        "auction": [
            "auction house", "bidding", "auction service", "online auction"
        ],
        "money_changer": [
            "money changer", "money transfer agent", "currency exchange agent"
        ],
        "offshore": [
            "offshore corporation", "offshore company", "offshore entity"
        ],
        "crowdsourcing": [
            "crowdsourcing platform", "crowdsourcing service", "crowdfunding"
        ],
        "antiques_art": [
            "antique dealer", "art dealer", "antique shop", "art shop"
        ],
        "gems_jewellery": [
            "gems", "jewellery", "precious metals", "bullion", "gem dealer",
            "jewellery dealer", "precious metal dealer"
        ],
        "embassies": [
            "embassy", "consulate", "diplomatic service"
        ],
        "business_correspondent": [
            "business correspondent", "aeps", "dmt", "payout service", "bc service"
        ],
        "digital_lending": [
            "digital lending", "loan app", "lending app", "online lending",
            "digital loan", "instant loan"
        ],
        "gift_cards_forex": [
            "gift card forex", "foreign currency gift card", "forex gift card"
        ],
        "video_chatting": [
            "video chat app", "dubious video chat", "video chatting app", "chat app"
        ],
        "spam": [
            "spam", "email list", "bulk marketing", "unsolicited email",
            "telemarketing", "spam software", "bulk email"
        ],
        "miracle_cures": [
            "miracle cure", "quick fix", "unsubstantiated cure", "miracle remedy",
            "quick health fix", "instant cure"
        ],
        "offensive_goods": [
            "defamation", "slander", "hate speech", "violent acts", "intolerance",
            "discrimination", "offensive material", "hate material"
        ],
        "illegal_goods": [
            "illegal goods", "contraband", "illegal products", "prohibited goods"
        ]
    }
    
    # V2.2: Generic keywords that require additional context to avoid false positives
    # These single words commonly appear in innocent contexts (colors, products, auth)
    GENERIC_KEYWORDS_REQUIRE_CONTEXT = {
        # crypto category - generic words that need "crypto" context
        'coin': ['crypto', 'bitcoin', 'digital', 'virtual'],
        'wallet': ['crypto', 'bitcoin', 'digital', 'blockchain'],
        'token': ['crypto', 'nft', 'blockchain', 'ico'],
        # alcohol category - color names
        'wine': ['alcohol', 'drink', 'beverage', 'liquor', 'bar'],
        # These are too generic on their own
        'spirits': ['alcohol', 'drink', 'beverage', 'liquor'],
    }
    
    @staticmethod
    def _normalize_keyword_for_matching(keyword: str) -> str:
        """
        Normalize keyword for flexible matching
        Converts hyphens to spaces and handles variations
        """
        # Replace hyphens with spaces for flexible matching
        normalized = keyword.replace('-', ' ')
        return normalized
    
    @staticmethod
    def _is_boilerplate_context(keyword_pos: int, page_text: str) -> bool:
        """
        V2.2.1: Check if a keyword appears in embedded boilerplate/payment gateway text.
        
        Many e-commerce sites embed third-party payment gateway terms that mention
        prohibited categories. This method detects such contexts to filter false positives.
        
        Args:
            keyword_pos: Position of keyword in text
            page_text: Full page text (lowercased)
            
        Returns:
            True if keyword appears in boilerplate context (likely false positive)
        """
        # Check 300 chars before and after keyword for boilerplate patterns
        context_start = max(0, keyword_pos - 300)
        context_end = min(len(page_text), keyword_pos + 300)
        context_text = page_text[context_start:context_end]
        
        for pattern in ContentAnalyzer.BOILERPLATE_PATTERNS:
            if re.search(pattern, context_text, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def _requires_context_validation(keyword: str, page_text: str) -> bool:
        """
        V2.2: Check if a generic keyword has sufficient context to be a true positive.
        
        For generic keywords like "coin", "wallet", "wine" that commonly appear in
        innocent contexts (e-commerce products, colors), we require additional
        contextual keywords to be present in the same page.
        
        Returns:
            True if the keyword should be considered a valid match
            False if it's likely a false positive (missing required context)
        """
        keyword_lower = keyword.lower()
        
        # Check if this keyword requires context validation
        required_context = ContentAnalyzer.GENERIC_KEYWORDS_REQUIRE_CONTEXT.get(keyword_lower)
        if not required_context:
            # Not a generic keyword - always valid
            return True
        
        # Check if any required context word is present on the page
        for context_word in required_context:
            if context_word in page_text:
                return True  # Context found - valid match
        
        # No context found - likely false positive
        return False
    
    @staticmethod
    def _match_keyword(keyword: str, page_text: str) -> bool:
        """
        Match keyword in page text with flexible hyphen/space handling
        
        Args:
            keyword: Keyword to search for (may contain hyphens)
            page_text: Text to search in (lowercased)
            
        Returns:
            True if keyword is found
        """
        # Direct match (exact substring)
        if keyword in page_text:
            return True
        
        # Normalize hyphenated keywords to match space-separated text
        # e.g., "sports-betting" should match "sports betting" or "sports bets"
        normalized_keyword = ContentAnalyzer._normalize_keyword_for_matching(keyword)
        if normalized_keyword in page_text:
            return True
        
        # For multi-word keywords, also check if individual words appear together
        # This handles cases like "online gambling" matching "online gambling sites"
        if ' ' in normalized_keyword:
            words = normalized_keyword.split()
            if len(words) >= 2:
                # Check if all words appear in sequence (within reasonable distance)
                # Simple approach: check if all words appear in the text
                if all(word in page_text for word in words):
                    # Use regex to check if words appear close together (within 50 chars)
                    pattern = r'\b' + r'\b.*\b'.join(re.escape(word) for word in words) + r'\b'
                    if re.search(pattern, page_text, re.IGNORECASE):
                        return True
        
        return False
    
    @staticmethod
    def _classify_intent(
        keyword: str,
        page_text: str,
        keyword_pos: int,
        page_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Classify the intent of a keyword match as prohibitive, promotional, or neutral.
        
        V2.2.1: Also checks for boilerplate context (embedded payment gateway terms).
        
        Looks at surrounding context (150 chars before keyword) to detect prohibitive
        phrases like "we do not allow", "is prohibited", etc.
        
        Args:
            keyword: The matched keyword
            page_text: Full page text (lowercased)
            keyword_pos: Position of keyword in text
            page_type: Type of page ('privacy_policy', 'terms_conditions', etc.)
            
        Returns:
            Dict with 'intent' ('prohibitive', 'promotional', 'neutral', 'boilerplate') and 'intent_context'
        """
        # Default to neutral
        intent = "neutral"
        intent_context = ""
        
        # V2.2.1: First check for boilerplate context (embedded payment gateway terms)
        # This is the most reliable indicator of a false positive
        if ContentAnalyzer._is_boilerplate_context(keyword_pos, page_text):
            return {
                "intent": "boilerplate",
                "intent_context": "Keyword found in embedded payment gateway/merchant agreement text"
            }
        
        # Get context window: 150 chars before and 50 chars after keyword
        context_start = max(0, keyword_pos - 150)
        context_end = min(len(page_text), keyword_pos + len(keyword) + 50)
        context_text = page_text[context_start:context_end]
        
        # Check for prohibitive patterns in the context
        for pattern in ContentAnalyzer.PROHIBITIVE_PATTERNS:
            match = re.search(pattern, context_text, re.IGNORECASE)
            if match:
                intent = "prohibitive"
                # Extract a meaningful snippet around the prohibitive phrase
                snippet_start = max(0, match.start() - 20)
                snippet_end = min(len(context_text), context_end - context_start)
                intent_context = context_text[snippet_start:snippet_end].strip()
                if len(intent_context) > 150:
                    intent_context = intent_context[:147] + "..."
                break
        
        # If on a policy page and no prohibitive pattern found, 
        # still mark as "neutral" but don't assume promotional
        # (policy pages mentioning keywords aren't necessarily promotional)
        if intent == "neutral" and page_type in ContentAnalyzer.POLICY_PAGE_TYPES:
            # V2.2.1: Policy pages get benefit of doubt - mark as prohibitive
            # since they typically mention restricted items in informational context
            intent = "prohibitive"
            intent_context = f"Found on policy page ({page_type}) - likely informational"
        
        # If not on a policy page and no prohibitive pattern, could be promotional
        # But we stay conservative and mark as neutral unless clearly promotional
        # (promotional detection would require additional patterns like "try our", "best deals", etc.)
        
        return {
            "intent": intent,
            "intent_context": intent_context
        }
    
    @staticmethod
    def analyze_content_risk(
        page_text: str,
        page_url: Optional[str] = None,
        page_type: Optional[str] = None,
        multi_page_corroboration: bool = False
    ) -> Dict[str, any]:
        """
        Analyze content for risks with context and intent awareness.
        Per PRD V2.1.1: Rule-based keyword detection (non-semantic).
        Each risk flag must include: triggering keyword, page URL, text snippet.
        Severity capped unless corroborated by multiple pages.
        
        Enhanced: Now classifies intent (prohibitive vs promotional) and includes
        page_type context to reduce false positives from legal boilerplate.
        
        Args:
            page_text: Full page text (lowercased)
            page_url: URL of the page (for evidence)
            page_type: Type of page ('privacy_policy', 'terms_conditions', 'product', etc.)
            multi_page_corroboration: True if risk found on multiple pages
            
        Returns:
            Dict with risk analysis including evidence, page_type, and intent metadata
        """
        # Ensure page_text is lowercased
        if not isinstance(page_text, str):
            page_text = str(page_text)
        page_text_lower = page_text.lower()
        
        # Per PRD: Explicitly label as rule-based
        detection_method = "Rule-based content keyword detection (non-semantic)"
        
        # Check for lorem ipsum
        dummy_words_found = []
        dummy_evidence = []
        for pattern in ContentAnalyzer.LOREM_PATTERNS:
            match = re.search(pattern, page_text_lower)
            if match:
                dummy_words_found.append(pattern)
                # Extract snippet around match (50 chars before/after)
                start = max(0, match.start() - 50)
                end = min(len(page_text), match.end() + 50)
                snippet = page_text[start:end].strip()
                if len(snippet) > 200:
                    snippet = snippet[:197] + "..."
                
                dummy_evidence.append({
                    "triggering_rule": f"Lorem ipsum pattern: {pattern}",
                    "evidence_snippet": snippet,
                    "page_url": page_url or "unknown",
                    "confidence": 100.0  # Pattern matching is deterministic
                })
        
        # Check for restricted keywords
        restricted_found = []
        for category, keywords in ContentAnalyzer.RESTRICTED_KEYWORDS.items():
            for keyword in keywords:
                if ContentAnalyzer._match_keyword(keyword, page_text_lower):
                    # V2.2: Check if generic keyword has sufficient context
                    if not ContentAnalyzer._requires_context_validation(keyword, page_text_lower):
                        # Skip - generic keyword without supporting context (likely false positive)
                        continue
                    
                    # Extract snippet around keyword (100 chars before/after)
                    keyword_lower = keyword.lower()
                    keyword_pos = page_text_lower.find(keyword_lower)
                    if keyword_pos >= 0:
                        start = max(0, keyword_pos - 100)
                        end = min(len(page_text), keyword_pos + len(keyword) + 100)
                        snippet = page_text[start:end].strip()
                        if len(snippet) > 200:
                            snippet = snippet[:197] + "..."
                    else:
                        snippet = f"Keyword '{keyword}' found in {category} category"
                        keyword_pos = 0  # Fallback for intent classification
                    
                    # Classify intent (prohibitive vs promotional)
                    intent_result = ContentAnalyzer._classify_intent(
                        keyword, page_text_lower, keyword_pos, page_type
                    )
                    intent = intent_result["intent"]
                    intent_context = intent_result["intent_context"]
                    
                    # Per PRD: Cap severity unless corroborated by multiple pages
                    # V2.2.1: Enhanced severity logic with boilerplate detection
                    severity = "moderate"
                    is_policy_page = page_type in ContentAnalyzer.POLICY_PAGE_TYPES
                    
                    if intent == "boilerplate":
                        # V2.2.1: Boilerplate = embedded third-party terms, not real risk
                        severity = "info"
                    elif intent == "prohibitive":
                        # Prohibitive intent = informational only
                        severity = "info"
                    elif multi_page_corroboration:
                        if category in ['gambling', 'adult', 'child_pornography']:
                            severity = "critical"
                        elif category in ['pharmacy', 'crypto']:
                            severity = "moderate"
                    else:
                        severity = "moderate"  # Cap at moderate unless corroborated
                    
                    restricted_found.append({
                        "category": category,
                        "keyword": keyword,
                        "page_type": page_type,  # NEW: Include page context
                        "intent": intent,  # NEW: 'prohibitive', 'promotional', or 'neutral'
                        "intent_context": intent_context,  # NEW: Surrounding text that determined intent
                        "evidence": {
                            "source_url": page_url or "unknown",
                            "triggering_rule": f"Rule-based keyword matching: '{keyword}' in category '{category}'",
                            "evidence_snippet": snippet,
                            "severity": severity,
                            "confidence": 50.0,  # Rule-based has moderate confidence
                            "corroborated": multi_page_corroboration
                        }
                    })
        
        # Calculate risk score - exclude non-risk items
        # V2.2.1: Count items that should actually contribute to risk score
        # Exclude: boilerplate, prohibitive intent
        risk_contributing_items = [
            item for item in restricted_found 
            if item.get("intent") not in ("prohibitive", "boilerplate")
        ]
        policy_mentions = [
            item for item in restricted_found
            if item.get("intent") in ("prohibitive", "boilerplate")
        ]
        
        risk_score = len(risk_contributing_items) * 20 + (50 if len(dummy_words_found) > 0 else 0)
        
        return {
            "detection_method": detection_method,  # Per PRD: Explicitly label as rule-based
            "dummy_words_detected": len(dummy_words_found) > 0,
            "dummy_words": dummy_words_found,
            "dummy_words_evidence": dummy_evidence,
            "restricted_keywords_found": restricted_found,
            "risk_score": risk_score,
            "signal_type": "advisory",  # Per PRD classification
            # NEW: Metadata about intent-aware processing
            "policy_mentions_count": len(policy_mentions),  # Keywords in prohibitive context on policy pages
            "risk_contributing_count": len(risk_contributing_items),  # Keywords that actually add to risk
            "page_type": page_type  # Echo back the page type for transparency
        }

    @staticmethod
    def analyze_content_risk_multi_pages(pages: List[Dict[str, str]]) -> Dict[str, any]:
        """
        Analyze content risks across multiple pages (coverage-first).

        Per plan: analyze all fetched pages, return per-page findings + rollups, and
        compute corroboration across pages while preserving evidence (source_url/snippet).

        Args:
            pages: list of {"url": str, "text": str, "page_type": Optional[str]}

        Returns:
            Dict suitable for report output.
        """
        safe_pages: List[Dict[str, any]] = []
        for p in pages or []:
            if not isinstance(p, dict):
                continue
            safe_pages.append(
                {
                    "url": p.get("url") or "unknown",
                    "text": p.get("text") or "",
                    "page_type": p.get("page_type") or None,
                    "render_type": p.get("render_type") or "http",
                }
            )
        safe_pages.sort(key=lambda p: p["url"])

        # First pass: category corroboration (category -> urls)
        # V2.2: Include context validation to avoid false positive corroboration
        category_to_urls: Dict[str, set] = {}
        for p in safe_pages:
            url = p["url"]
            text_lower = (p["text"] or "").lower()
            for category, keywords in ContentAnalyzer.RESTRICTED_KEYWORDS.items():
                for keyword in keywords:
                    if ContentAnalyzer._match_keyword(keyword, text_lower):
                        # V2.2: Skip generic keywords without supporting context
                        if not ContentAnalyzer._requires_context_validation(keyword, text_lower):
                            continue
                        category_to_urls.setdefault(category, set()).add(url)
                        break
        corroborated_categories = {c for c, urls in category_to_urls.items() if len(urls) > 1}

        per_page_findings: List[Dict[str, any]] = []
        flattened_restricted: List[Dict[str, any]] = []
        dummy_pages_count = 0
        dummy_patterns_all: List[str] = []
        dummy_evidence_all: List[Dict[str, any]] = []
        policy_mentions_total = 0
        risk_contributing_total = 0

        for p in safe_pages:
            url = p["url"]
            text = p["text"] or ""
            page_type = p.get("page_type")
            render_type = p.get("render_type") or "http"
            single = ContentAnalyzer.analyze_content_risk(
                text,
                page_url=url,
                page_type=page_type,
                multi_page_corroboration=False,  # corroboration handled per-category below
            )

            # Re-write corroboration flags/severity per category (more precise than a single boolean)
            page_restricted = single.get("restricted_keywords_found", []) or []
            for item in page_restricted:
                cat = item.get("category")
                if not cat:
                    continue
                is_corroborated = cat in corroborated_categories
                ev = item.get("evidence", {}) if isinstance(item.get("evidence"), dict) else {}
                ev["corroborated"] = is_corroborated
                # Provenance: how the page content was obtained (http/js/cache)
                ev["detection_method"] = render_type
                # Severity caps: only allow "critical" when corroborated AND severe category
                if is_corroborated and cat in ["gambling", "adult", "child_pornography"]:
                    ev["severity"] = "critical"
                else:
                    ev["severity"] = "moderate"
                item["evidence"] = ev
                flattened_restricted.append(item)

            if single.get("dummy_words_detected"):
                dummy_pages_count += 1
                dummy_patterns_all.extend(single.get("dummy_words", []) or [])
                dummy_evidence_all.extend(single.get("dummy_words_evidence", []) or [])

            policy_mentions_total += int(single.get("policy_mentions_count", 0) or 0)
            risk_contributing_total += int(single.get("risk_contributing_count", 0) or 0)

            per_page_findings.append(
                {
                    "page_url": url,
                    "page_type": page_type,
                    "render_type": render_type,
                    "dummy_words_detected": bool(single.get("dummy_words_detected")),
                    "dummy_words": single.get("dummy_words", []),
                    "dummy_words_evidence": single.get("dummy_words_evidence", []),
                    "restricted_keywords_found": page_restricted,
                    "risk_contributing_count": single.get("risk_contributing_count", 0),
                    "policy_mentions_count": single.get("policy_mentions_count", 0),
                }
            )

        # Deterministic scoring: count unique (url, category, keyword)
        uniq = set()
        for item in flattened_restricted:
            ev = item.get("evidence", {}) if isinstance(item.get("evidence"), dict) else {}
            uniq.add((ev.get("source_url", ""), item.get("category", ""), item.get("keyword", "")))

        risk_score = len(uniq) * 20 + (50 * dummy_pages_count)

        return {
            "detection_method": "Rule-based content keyword detection (non-semantic)",
            "pages_analyzed": len(safe_pages),
            "per_page_findings": per_page_findings,
            "dummy_words_detected": dummy_pages_count > 0,
            "dummy_words": sorted(list(set(dummy_patterns_all))),
            "dummy_words_evidence": dummy_evidence_all,
            "restricted_keywords_found": sorted(
                flattened_restricted,
                key=lambda i: (
                    i.get("category", ""),
                    i.get("keyword", ""),
                    (i.get("evidence", {}) or {}).get("source_url", ""),
                ),
            ),
            "corroboration": {k: sorted(list(v)) for k, v in sorted(category_to_urls.items(), key=lambda kv: kv[0])},
            "risk_score": risk_score,
            "signal_type": "advisory",
            "policy_mentions_count": policy_mentions_total,
            "risk_contributing_count": risk_contributing_total,
        }
    
    @staticmethod
    def detect_product_indicators(page_text: str) -> Dict[str, bool]:
        """
        Detect product/ecommerce indicators
        
        Args:
            page_text: Full page text (lowercased)
            
        Returns:
            Dict with product indicators
        """
        return {
            "has_products": "product" in page_text or "shop" in page_text,
            "has_pricing": "price" in page_text or "$" in page_text or "₹" in page_text,
            "has_cart": "add to cart" in page_text or "buy now" in page_text,
            "ecommerce_platform": "shopify" in page_text or "woocommerce" in page_text
        }
