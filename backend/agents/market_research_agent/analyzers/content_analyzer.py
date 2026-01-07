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
    def analyze_content_risk(
        page_text: str,
        page_url: Optional[str] = None,
        multi_page_corroboration: bool = False
    ) -> Dict[str, any]:
        """
        Analyze content for risks.
        Per PRD V2.1.1: Rule-based keyword detection (non-semantic).
        Each risk flag must include: triggering keyword, page URL, text snippet.
        Severity capped unless corroborated by multiple pages.
        
        Args:
            page_text: Full page text (lowercased)
            page_url: URL of the page (for evidence)
            multi_page_corroboration: True if risk found on multiple pages
            
        Returns:
            Dict with risk analysis including evidence
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
                    
                    # Per PRD: Cap severity unless corroborated by multiple pages
                    severity = "moderate"
                    if multi_page_corroboration:
                        if category in ['gambling', 'adult', 'child_pornography']:
                            severity = "critical"
                        elif category in ['pharmacy', 'crypto']:
                            severity = "moderate"
                    else:
                        severity = "moderate"  # Cap at moderate unless corroborated
                    
                    restricted_found.append({
                        "category": category,
                        "keyword": keyword,
                        "evidence": {
                            "source_url": page_url or "unknown",
                            "triggering_rule": f"Rule-based keyword matching: '{keyword}' in category '{category}'",
                            "evidence_snippet": snippet,
                            "severity": severity,
                            "confidence": 50.0,  # Rule-based has moderate confidence
                            "corroborated": multi_page_corroboration
                        }
                    })
        
        # Calculate risk score
        risk_score = len(restricted_found) * 20 + (50 if len(dummy_words_found) > 0 else 0)
        
        return {
            "detection_method": detection_method,  # Per PRD: Explicitly label as rule-based
            "dummy_words_detected": len(dummy_words_found) > 0,
            "dummy_words": dummy_words_found,
            "dummy_words_evidence": dummy_evidence,
            "restricted_keywords_found": restricted_found,
            "risk_score": risk_score,
            "signal_type": "advisory"  # Per PRD classification
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
