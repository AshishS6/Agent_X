"""
KYC Site Scan Input Schema
Defines the merchant input data structure for KYC screening
Per PRD Section 4: Required and Optional Inputs
"""

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator
from enum import Enum


class RiskTier(str, Enum):
    """Internal risk tier classification"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class OptionalMerchantData(BaseModel):
    """Optional merchant data that enhances screening accuracy"""
    mcc: Optional[str] = Field(
        default=None,
        description="Merchant Category Code (if available)",
        examples=["5411", "7372"]
    )
    country_of_incorporation: Optional[str] = Field(
        default=None,
        description="Country of incorporation (ISO 3166-1 alpha-2)",
        examples=["US", "IN", "GB"]
    )
    risk_tier: Optional[RiskTier] = Field(
        default=RiskTier.UNKNOWN,
        description="Internal risk tier classification"
    )


class MerchantKYCInput(BaseModel):
    """
    Required merchant input for KYC website screening.
    
    Per PRD Section 4:
    - All required fields must be provided
    - website_url must be valid and accessible
    - declared_products_services must have at least one entry
    """
    
    # Required fields
    merchant_legal_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Official registered legal name of the merchant",
        examples=["Acme Corporation Pvt Ltd", "TechStart Inc."]
    )
    
    registered_address: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Registered business address",
        examples=["123 Business Park, Suite 400, Mumbai, MH 400001, India"]
    )
    
    declared_business_type: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Type of business as declared by merchant",
        examples=["E-commerce", "SaaS", "Financial Services", "Retail"]
    )
    
    declared_products_services: List[str] = Field(
        ...,
        min_length=1,
        description="List of products/services the merchant claims to offer",
        examples=[["Clothing", "Accessories"], ["Software Subscriptions", "Cloud Hosting"]]
    )
    
    website_url: str = Field(
        ...,
        description="Primary website URL of the merchant",
        examples=["https://www.example.com", "https://shop.merchant.com"]
    )
    
    merchant_display_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display/brand name shown to customers",
        examples=["Acme Shop", "TechStart"]
    )
    
    # Optional fields
    optional_data: Optional[OptionalMerchantData] = Field(
        default=None,
        description="Optional merchant data for enhanced screening"
    )
    
    @field_validator('website_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL has proper scheme"""
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v
    
    @field_validator('declared_products_services')
    @classmethod
    def validate_products(cls, v: List[str]) -> List[str]:
        """Ensure at least one product/service is declared"""
        if not v or len(v) == 0:
            raise ValueError("At least one product/service must be declared")
        # Clean up entries
        return [p.strip() for p in v if p.strip()]
    
    @field_validator('merchant_legal_name', 'merchant_display_name', 'declared_business_type')
    @classmethod
    def validate_string_fields(cls, v: str) -> str:
        """Clean up string fields"""
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "merchant_legal_name": "TechStart Solutions Pvt Ltd",
                "registered_address": "Tower A, Tech Park, Whitefield, Bangalore, KA 560066, India",
                "declared_business_type": "SaaS",
                "declared_products_services": ["CRM Software", "Marketing Automation", "Analytics Dashboard"],
                "website_url": "https://www.techstart.io",
                "merchant_display_name": "TechStart",
                "optional_data": {
                    "mcc": "7372",
                    "country_of_incorporation": "IN",
                    "risk_tier": "LOW"
                }
            }
        }

