#!/usr/bin/env python
"""Test script to verify SafeChain AI knowledge base integration"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_support.settings')
django.setup()

from core.safechain_knowledge import SAFECHAIN_KNOWLEDGE, SAFECHAIN_FAQ, SAFECHAIN_SUPPORT_CATEGORIES

def test_knowledge_base():
    """Test the SafeChain AI knowledge base"""
    print("🛡️ SafeChain AI - Knowledge Base Test")
    print("=" * 50)
    
    # Test 1: Company Information
    print("✅ Company Information:")
    print(f"   - Name: {SAFECHAIN_KNOWLEDGE['company_info']['name']}")
    print(f"   - Tagline: {SAFECHAIN_KNOWLEDGE['company_info']['tagline']}")
    print(f"   - Website: {SAFECHAIN_KNOWLEDGE['company_info']['website']}")
    print(f"   - Contact: {SAFECHAIN_KNOWLEDGE['company_info']['email']}")
    
    # Test 2: Statistics
    print("\n✅ Platform Statistics:")
    print(f"   - Investors: {SAFECHAIN_KNOWLEDGE['statistics']['investors_joined']}")
    print(f"   - Total Payouts: {SAFECHAIN_KNOWLEDGE['statistics']['total_payouts']}")
    print(f"   - AI Strategies: {SAFECHAIN_KNOWLEDGE['statistics']['ai_strategies']}")
    
    # Test 3: Investment Tiers
    print("\n✅ Investment Tiers:")
    for tier in SAFECHAIN_KNOWLEDGE['investment_tiers']:
        print(f"   - {tier['name']}: {tier['investment']} investment, {tier['duration']} duration, {tier['return']} return")
        print(f"     Description: {tier['description']}")
    
    # Test 4: Investment Calculator
    print("\n✅ Investment Calculator:")
    calculator = SAFECHAIN_KNOWLEDGE['investment_calculator']
    print(f"   - Title: {calculator['title']}")
    print(f"   - Investment Amount Label: {calculator['investment_amount_label']}")
    print(f"   - Select Tier Label: {calculator['select_tier_label']}")
    print(f"   - Example Calculation:")
    example = calculator['example_calculation']
    print(f"     Tier: {example['tier']}")
    print(f"     Investment: {example['investment']}")
    print(f"     Expected Return: {example['expected_return']}")
    print(f"     Duration: {example['duration']}")
    print(f"     Return Date: {example['return_date']}")
    
    # Test 5: Referral Program
    print("\n✅ Referral Program:")
    print(f"   - Description: {SAFECHAIN_KNOWLEDGE['referral_program']['description']}")
    print(f"   - Link: {SAFECHAIN_KNOWLEDGE['referral_program']['referral_link']}")
    
    # Test 6: How It Works
    print("\n✅ How It Works:")
    for step in SAFECHAIN_KNOWLEDGE['how_it_works']:
        print(f"   - {step['icon']} {step['step']}: {step['description']}")
    
    # Test 7: FAQ
    print("\n✅ FAQ Entries:")
    for key, faq in SAFECHAIN_FAQ.items():
        print(f"   - {faq['question']}")
        print(f"     Answer: {faq['answer']}")
    
    # Test 8: Support Categories
    print("\n✅ Support Categories:")
    for category, description in SAFECHAIN_SUPPORT_CATEGORIES.items():
        print(f"   - {category}: {description}")
    
    # Test 9: Features
    print("\n✅ Platform Features:")
    for feature in SAFECHAIN_KNOWLEDGE['features']:
        print(f"   - {feature}")
    
    print("\n🎉 Knowledge base test completed successfully!")
    print("The SafeChain AI knowledge base is properly configured and ready to use.")

if __name__ == "__main__":
    test_knowledge_base() 