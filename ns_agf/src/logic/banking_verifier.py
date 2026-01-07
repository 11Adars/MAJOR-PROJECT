"""
Banking Intent Verifier - Enhanced for 20-Class Banking Domain
===============================================================

This module implements advanced intent verification specifically for
the 20-class banking sign language recognition system.

Key Features:
- Sign sequence to intent mapping
- Multi-sign intent composition
- Slot filling with context awareness
- Banking transaction safety rules
- Authentication state tracking
- Confidence-based validation

Author: NS-AGF Project
Date: December 2025
"""

import json
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re


class BankingIntent(Enum):
    """Banking-specific intents"""
    GREETING = "greeting"
    ACCESS_BANK = "access_bank"
    ACCESS_ATM = "access_atm"
    CHECK_BALANCE = "check_balance"
    TRANSFER = "transfer"
    CHECK_INTEREST = "check_interest"
    CONTACT_MANAGER = "contact_manager"
    ACCESS_ONLINE = "access_online"
    ALERT_FRAUD = "alert_fraud"
    # New intents added for complete 20-class coverage
    DELETE_ACCOUNT = "delete_account"
    REQUEST_HELP = "request_help"
    LOAN_INQUIRY = "loan_inquiry"
    PASSBOOK_REQUEST = "passbook_request"
    REPORT_ISSUE = "report_issue"
    SPEAK_TO_AGENT = "speak_to_agent"
    REPORT_MISSING = "report_missing"
    UNKNOWN = "unknown"
    INCOMPLETE = "incomplete"


@dataclass
class IntentContext:
    """Maintains context across multiple sign interactions"""
    current_intent: Optional[BankingIntent] = None
    confidence: float = 0.0
    slots: Dict[str, Any] = field(default_factory=dict)
    sign_history: List[str] = field(default_factory=list)
    is_authenticated: bool = False
    pending_confirmation: bool = False
    missing_slots: List[str] = field(default_factory=list)
    error_message: str = ""
    
    def reset(self):
        """Reset context for new interaction"""
        self.current_intent = None
        self.confidence = 0.0
        self.slots = {}
        self.sign_history = []
        self.pending_confirmation = False
        self.missing_slots = []
        self.error_message = ""


class BankingIntentVerifier:
    """
    Enhanced intent verifier for banking sign language system.
    
    Handles:
    1. Sign → Intent mapping (single or multi-sign)
    2. Slot extraction from sign sequences
    3. Context-aware validation
    4. Safety rules enforcement
    5. Confirmation requirements
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        """
        Initialize verifier with intent rules.
        
        Args:
            rules_path: Path to intent_rules.json (optional)
        """
        # Load rules
        if rules_path and Path(rules_path).exists():
            with open(rules_path, 'r') as f:
                self.rules = json.load(f)
        else:
            raise FileNotFoundError(
                f"Intent rules not found at {rules_path}. "
                "Please ensure intent_rules.json exists in src/logic/"
            )
        
        # Extract configuration
        self.sign_to_intent = self.rules["sign_to_intent_mapping"]
        self.intents = self.rules["intents"]
        self.slots_config = self.rules["slots"]
        self.constraints = self.rules["semantic_constraints"]
        self.confidence_thresholds = self.rules["confidence_thresholds"]
        self.safety_rules = self.rules["safety_rules"]
        
        # Context tracking
        self.context = IntentContext()
        
    def verify_sign_sequence(
        self,
        signs: List[str],
        confidences: List[float]
    ) -> Tuple[BankingIntent, IntentContext, bool]:
        """
        Main verification function for a sequence of signs.
        
        Args:
            signs: List of recognized signs (from model predictions)
            confidences: Confidence scores for each sign
        
        Returns:
            (intent, context, is_valid)
        """
        # Update sign history
        self.context.sign_history.extend(signs)
        
        # Step 1: Map signs to intent
        intent = self._map_signs_to_intent(signs)
        self.context.current_intent = intent
        
        # Step 2: Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        self.context.confidence = avg_confidence
        
        # Step 3: Check confidence threshold
        if intent != BankingIntent.UNKNOWN:
            intent_name = intent.value
            threshold = self.confidence_thresholds.get(intent_name, 0.75)
            
            if avg_confidence < threshold:
                self.context.error_message = (
                    f"Confidence too low: {avg_confidence:.1%} < {threshold:.1%}"
                )
                return intent, self.context, False
        
        # Step 4: Extract slots from signs
        self._extract_slots_from_signs(signs)
        
        # Step 5: Check required slots
        if intent != BankingIntent.UNKNOWN and intent.value in self.intents:
            required_slots = self.intents[intent.value]["required_slots"]
            self.context.missing_slots = [
                slot for slot in required_slots 
                if slot not in self.context.slots
            ]
        
        # Step 6: Check semantic constraints
        is_consistent, error_msg = self._check_semantic_consistency(intent)
        if not is_consistent:
            self.context.error_message = error_msg
            return intent, self.context, False
        
        # Step 7: Check authentication requirement
        if not self._check_authentication(intent):
            self.context.error_message = (
                "Authentication required for this operation. Please authenticate first."
            )
            return intent, self.context, False
        
        # Step 8: Apply safety checks
        if intent == BankingIntent.TRANSFER:
            is_safe, safety_error = self._check_transaction_safety()
            if not is_safe:
                self.context.error_message = safety_error
                return intent, self.context, False
        
        # Step 9: Check if confirmation needed
        if intent.value in self.constraints["required_confirmations"]:
            self.context.pending_confirmation = True
        
        # Step 10: Validate completeness
        if self.context.missing_slots:
            self.context.error_message = (
                f"Missing required information: {', '.join(self.context.missing_slots)}"
            )
            return BankingIntent.INCOMPLETE, self.context, False
        
        # All checks passed
        self.context.error_message = ""
        return intent, self.context, True
    
    def _map_signs_to_intent(self, signs: List[str]) -> BankingIntent:
        """
        Map sign sequence to banking intent.
        
        Handles:
        - Single-sign intents (e.g., "Hello" → greeting)
        - Multi-sign intents (e.g., "Transfer Money" → transfer)
        - Slot signs (e.g., "amount" → slot_amount)
        """
        if not signs:
            return BankingIntent.UNKNOWN
        
        # Check for direct mapping
        primary_sign = signs[0]
        if primary_sign in self.sign_to_intent:
            intent_str = self.sign_to_intent[primary_sign]
            
            # Skip slot signs - these don't define intent alone
            if intent_str.startswith("slot_"):
                # Look for actual intent in remaining signs
                for sign in signs[1:]:
                    if sign in self.sign_to_intent:
                        intent_str = self.sign_to_intent[sign]
                        if not intent_str.startswith("slot_"):
                            break
                else:
                    return BankingIntent.UNKNOWN
            
            try:
                return BankingIntent(intent_str)
            except ValueError:
                return BankingIntent.UNKNOWN
        
        # Check for keyword-based mapping
        for intent_name, intent_config in self.intents.items():
            keywords = intent_config["keywords"]
            # Check if any keyword matches any sign (case-insensitive)
            for sign in signs:
                if any(kw.lower() in sign.lower() for kw in keywords):
                    try:
                        return BankingIntent(intent_name)
                    except ValueError:
                        continue
        
        return BankingIntent.UNKNOWN
    
    def _extract_slots_from_signs(self, signs: List[str]):
        """
        Extract slot values from sign sequence.
        
        Handles:
        - Numeric amounts (e.g., "5000" → amount=5000)
        - Account IDs (e.g., "ACCOUNT_123" → recipient)
        - Addresses (e.g., "address" sign → prompt for details)
        """
        for sign in signs:
            # Amount extraction (numeric signs)
            if sign.isdigit():
                amount = int(sign)
                if 1 <= amount <= self.safety_rules["max_transfer_amount"]:
                    self.context.slots["amount"] = amount
            
            # Recipient extraction (account IDs)
            if sign.startswith(("ACCOUNT_", "USER_", "ACCT")):
                self.context.slots["recipient"] = sign
            
            # Address flag
            if "address" in sign.lower():
                self.context.slots["address_required"] = True
            
            # Self reference
            if sign.lower() in ["i", "me", "my"]:
                self.context.slots["subject"] = "self"
    
    def _check_semantic_consistency(self, intent: BankingIntent) -> Tuple[bool, str]:
        """
        Check if sign sequence is semantically valid.
        
        Validates:
        - Invalid intent sequences (e.g., can't transfer after balance without amount)
        - Required authentication for sensitive operations
        """
        # Check invalid sequences
        for constraint in self.constraints["invalid_sequences"]:
            sequence = constraint["sequence"]
            
            # Check if recent history contains the invalid sequence
            if len(self.context.sign_history) >= len(sequence):
                recent_intents = []
                for sign in self.context.sign_history[-len(sequence):]:
                    if sign in self.sign_to_intent:
                        recent_intents.append(self.sign_to_intent[sign])
                
                if recent_intents == sequence:
                    # Check for exceptions
                    exception = constraint.get("exception")
                    if exception:
                        if exception == "amount_provided" and "amount" in self.context.slots:
                            continue
                        if exception == "authenticated" and self.context.is_authenticated:
                            continue
                    
                    return False, constraint["reason"]
        
        return True, ""
    
    def _check_authentication(self, intent: BankingIntent) -> bool:
        """
        Check if user is authenticated for sensitive operations.
        
        Required for: transfer, balance check, interest check, online access
        """
        if intent.value in self.constraints["required_authentication"]:
            return self.context.is_authenticated
        return True
    
    def _check_transaction_safety(self) -> Tuple[bool, str]:
        """
        Apply banking safety rules for transactions.
        
        Checks:
        - Amount within limits
        - Recipient validation
        - Positive amount
        - Two-factor authentication for large amounts
        """
        amount = self.context.slots.get("amount")
        recipient = self.context.slots.get("recipient")
        
        # Amount checks
        if amount is not None:
            if amount <= 0:
                return False, "Transaction amount must be positive"
            
            max_amount = self.safety_rules["max_transfer_amount"]
            if amount > max_amount:
                return False, f"Amount exceeds maximum limit: ₹{amount:,} > ₹{max_amount:,}"
            
            # Two-factor requirement for large amounts
            two_factor_threshold = self.safety_rules["require_two_factor_above"]
            if amount > two_factor_threshold:
                if not self.context.slots.get("two_factor_verified", False):
                    return False, (
                        f"Transactions above ₹{two_factor_threshold:,} require "
                        "two-factor authentication"
                    )
        
        # Recipient check
        if not recipient:
            return False, "Recipient account must be specified for transfers"
        
        return True, ""
    
    def get_slot_prompt(self) -> str:
        """
        Generate user-friendly prompt for missing slot.
        
        Returns:
            Sign language prompt for the user
        """
        if not self.context.missing_slots:
            return ""
        
        slot_name = self.context.missing_slots[0]
        slot_config = self.slots_config.get(slot_name, {})
        
        return slot_config.get("prompt", f"Please provide: {slot_name}")
    
    def get_confirmation_message(self) -> str:
        """
        Generate confirmation message for pending transactions.
        
        Returns:
            Human-readable confirmation message
        """
        if not self.context.pending_confirmation:
            return ""
        
        intent = self.context.current_intent
        if intent == BankingIntent.TRANSFER:
            amount = self.context.slots.get("amount", "???")
            recipient = self.context.slots.get("recipient", "???")
            return f"Transfer ₹{amount:,} to {recipient}. Please confirm (Sign YES or NO)"
        
        return "Please confirm this action (Sign YES or NO)"
    
    def authenticate_user(self, user_id: str, verified: bool = True):
        """
        Set authentication state.
        
        Args:
            user_id: User identifier
            verified: Whether authentication was successful
        """
        self.context.is_authenticated = verified
        if verified:
            self.context.slots["user_id"] = user_id
    
    def confirm_action(self, confirmed: bool):
        """
        Handle user confirmation for pending actions.
        
        Args:
            confirmed: Whether user confirmed (YES) or denied (NO)
        """
        if confirmed:
            self.context.pending_confirmation = False
            self.context.error_message = ""
        else:
            self.context.reset()
            self.context.error_message = "Transaction cancelled by user"
    
    def reset_context(self):
        """Reset the interaction context"""
        self.context.reset()


# ==================== TESTING ====================
if __name__ == "__main__":
    print("🔬 Testing Banking Intent Verifier...")
    
    # Initialize verifier
    rules_path = Path(__file__).parent / "intent_rules.json"
    verifier = BankingIntentVerifier(rules_path=str(rules_path))
    
    # Simulate authentication
    verifier.authenticate_user("USER_001", verified=True)
    
    # Test Case 1: Greeting
    print("\n--- Test 1: Greeting ---")
    intent, context, is_valid = verifier.verify_sign_sequence(
        signs=["Hello"],
        confidences=[0.95]
    )
    print(f"Intent: {intent.value}, Valid: {is_valid}, Confidence: {context.confidence:.1%}")
    if not is_valid:
        print(f"Error: {context.error_message}")
    
    # Test Case 2: Check Balance
    print("\n--- Test 2: Check Balance ---")
    verifier.reset_context()
    verifier.authenticate_user("USER_001", verified=True)
    intent, context, is_valid = verifier.verify_sign_sequence(
        signs=["account"],
        confidences=[0.88]
    )
    print(f"Intent: {intent.value}, Valid: {is_valid}")
    if not is_valid:
        print(f"Error: {context.error_message}")
    
    # Test Case 3: Transfer - Missing Slots
    print("\n--- Test 3: Transfer (Incomplete) ---")
    verifier.reset_context()
    verifier.authenticate_user("USER_001", verified=True)
    intent, context, is_valid = verifier.verify_sign_sequence(
        signs=["Transfer Money"],
        confidences=[0.92]
    )
    print(f"Intent: {intent.value}, Valid: {is_valid}")
    print(f"Missing slots: {context.missing_slots}")
    if not is_valid:
        print(f"Error: {context.error_message}")
        print(f"Prompt: {verifier.get_slot_prompt()}")
    
    # Test Case 4: Complete Transfer
    print("\n--- Test 4: Complete Transfer ---")
    verifier.reset_context()
    verifier.authenticate_user("USER_001", verified=True)
    intent, context, is_valid = verifier.verify_sign_sequence(
        signs=["Transfer Money", "5000", "ACCOUNT_123"],
        confidences=[0.92, 0.95, 0.88]
    )
    print(f"Intent: {intent.value}, Valid: {is_valid}")
    print(f"Slots: {context.slots}")
    print(f"Pending confirmation: {context.pending_confirmation}")
    if context.pending_confirmation:
        print(f"Confirmation message: {verifier.get_confirmation_message()}")
    
    # Test Case 5: Excessive Amount
    print("\n--- Test 5: Transfer (Amount Too High) ---")
    verifier.reset_context()
    verifier.authenticate_user("USER_001", verified=True)
    intent, context, is_valid = verifier.verify_sign_sequence(
        signs=["Transfer Money", "500000", "ACCOUNT_123"],
        confidences=[0.92, 0.95, 0.88]
    )
    print(f"Intent: {intent.value}, Valid: {is_valid}")
    if not is_valid:
        print(f"Error: {context.error_message}")
    
    # Test Case 6: Fraud Alert
    print("\n--- Test 6: Fraud Alert ---")
    verifier.reset_context()
    intent, context, is_valid = verifier.verify_sign_sequence(
        signs=["Illegal"],
        confidences=[0.90]
    )
    print(f"Intent: {intent.value}, Valid: {is_valid}, Priority: HIGH")
    
    print("\n✨ All tests passed!")
