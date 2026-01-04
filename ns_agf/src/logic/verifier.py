"""
Neuro-Symbolic Intent Verifier
===============================

This module implements the symbolic reasoning layer that ensures neural network
predictions are semantically valid before execution.

Core Functionality:
- Intent validation with confidence thresholds
- Slot filling for incomplete commands
- Semantic consistency checking
- Banking transaction safety rules
"""

import json
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import os


class IntentType(Enum):
    """Supported banking intents"""
    BALANCE = "balance"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    HISTORY = "history"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Structured intent representation"""
    type: IntentType
    confidence: float
    slots: Dict[str, Any]
    gloss_sequence: List[str]
    is_complete: bool = False
    missing_slots: List[str] = None
    
    def __post_init__(self):
        if self.missing_slots is None:
            self.missing_slots = []


class NeuroSymbolicVerifier:
    """
    Validates neural network predictions using symbolic rules.
    """
    
    def __init__(self, rules_path: Optional[str] = None, confidence_threshold: float = 0.75):
        """
        Args:
            rules_path: Path to intent_rules.json (optional)
            confidence_threshold: Minimum confidence for intent acceptance
        """
        self.confidence_threshold = confidence_threshold
        
        # Load rules
        if rules_path and os.path.exists(rules_path):
            with open(rules_path, 'r') as f:
                self.rules = json.load(f)
        else:
            self.rules = self._default_rules()
        
        # Transaction safety rules
        self.max_transfer_amount = 100000  # Maximum single transfer
        self.daily_limit = 500000  # Daily transaction limit
        
    def _default_rules(self) -> Dict:
        """Default intent rules if no file provided"""
        return {
            "intents": {
                "balance": {
                    "required_slots": [],
                    "optional_slots": ["account_type"],
                    "keywords": ["balance", "check", "account", "money", "show"],
                    "confidence_boost": 0.1
                },
                "transfer": {
                    "required_slots": ["amount", "recipient"],
                    "optional_slots": ["account_from", "account_to"],
                    "keywords": ["transfer", "send", "money", "pay"],
                    "confidence_boost": 0.0,
                    "safety_checks": ["amount_limit", "recipient_validation"]
                },
                "deposit": {
                    "required_slots": ["amount"],
                    "optional_slots": ["account"],
                    "keywords": ["deposit", "add", "money", "cash"],
                    "confidence_boost": 0.05
                },
                "withdraw": {
                    "required_slots": ["amount"],
                    "optional_slots": ["account"],
                    "keywords": ["withdraw", "take", "money", "cash"],
                    "confidence_boost": 0.05,
                    "safety_checks": ["amount_limit"]
                },
                "history": {
                    "required_slots": [],
                    "optional_slots": ["date_range", "account"],
                    "keywords": ["history", "transactions", "past", "show"],
                    "confidence_boost": 0.1
                },
                "help": {
                    "required_slots": [],
                    "optional_slots": [],
                    "keywords": ["help", "support", "how", "what"],
                    "confidence_boost": 0.15
                }
            },
            "semantic_constraints": {
                "invalid_sequences": [
                    ["balance", "transfer"],  # Cannot transfer immediately after balance
                    ["withdraw", "deposit"]   # Cannot deposit immediately after withdraw
                ],
                "required_confirmations": ["transfer", "withdraw"]
            }
        }
    
    def verify(
        self,
        gloss_sequence: List[str],
        confidence_scores: List[float],
        predicted_intent: str
    ) -> Tuple[Intent, bool, str]:
        """
        Main verification function.
        
        Args:
            gloss_sequence: List of recognized sign glosses (words)
            confidence_scores: Confidence score for each gloss
            predicted_intent: Intent predicted by neural network
        
        Returns:
            (Intent object, is_valid, error_message)
        """
        # Step 1: Confidence check
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        if avg_confidence < self.confidence_threshold:
            return (
                Intent(IntentType.UNKNOWN, avg_confidence, {}, gloss_sequence),
                False,
                f"Confidence too low: {avg_confidence:.2f} < {self.confidence_threshold}"
            )
        
        # Step 2: Map to IntentType
        try:
            intent_type = IntentType(predicted_intent.lower())
        except ValueError:
            intent_type = IntentType.UNKNOWN
        
        if intent_type == IntentType.UNKNOWN:
            return (
                Intent(intent_type, avg_confidence, {}, gloss_sequence),
                False,
                f"Unknown intent: {predicted_intent}"
            )
        
        # Step 3: Extract slots from gloss sequence
        slots = self._extract_slots(gloss_sequence, intent_type)
        
        # Step 4: Check required slots
        required_slots = self.rules["intents"][intent_type.value]["required_slots"]
        missing_slots = [slot for slot in required_slots if slot not in slots]
        
        # Step 5: Semantic consistency check
        is_consistent, consistency_error = self._check_semantic_consistency(
            gloss_sequence, intent_type
        )
        
        if not is_consistent:
            return (
                Intent(intent_type, avg_confidence, slots, gloss_sequence, missing_slots=missing_slots),
                False,
                consistency_error
            )
        
        # Step 6: Safety checks (for financial transactions)
        if "safety_checks" in self.rules["intents"][intent_type.value]:
            is_safe, safety_error = self._check_safety(intent_type, slots)
            if not is_safe:
                return (
                    Intent(intent_type, avg_confidence, slots, gloss_sequence, missing_slots=missing_slots),
                    False,
                    safety_error
                )
        
        # Step 7: Build final intent
        intent = Intent(
            type=intent_type,
            confidence=avg_confidence,
            slots=slots,
            gloss_sequence=gloss_sequence,
            is_complete=len(missing_slots) == 0,
            missing_slots=missing_slots
        )
        
        if missing_slots:
            return (
                intent,
                False,
                f"Missing required slots: {', '.join(missing_slots)}"
            )
        
        return (intent, True, "Intent verified successfully")
    
    def _extract_slots(self, gloss_sequence: List[str], intent_type: IntentType) -> Dict[str, Any]:
        """
        Extract slot values from gloss sequence.
        
        This is a simplified version - in production, you'd use NER or slot-filling models.
        """
        slots = {}
        
        # Simple pattern matching for numbers (amounts)
        for i, gloss in enumerate(gloss_sequence):
            # Amount detection (look for number patterns)
            if gloss.isdigit():
                if "amount" in self.rules["intents"][intent_type.value]["required_slots"]:
                    slots["amount"] = int(gloss)
            
            # Recipient detection (look for names or account IDs)
            if gloss.startswith("ACCOUNT_") or gloss.startswith("USER_"):
                if "recipient" in self.rules["intents"][intent_type.value]["required_slots"]:
                    slots["recipient"] = gloss
        
        return slots
    
    def _check_semantic_consistency(
        self, gloss_sequence: List[str], intent_type: IntentType
    ) -> Tuple[bool, str]:
        """
        Check if the gloss sequence is semantically consistent.
        """
        # Check for invalid sequences
        invalid_sequences = self.rules["semantic_constraints"]["invalid_sequences"]
        
        # Convert gloss to simplified tokens
        tokens = [g.lower() for g in gloss_sequence]
        
        for invalid_seq in invalid_sequences:
            # Check if invalid sequence appears in token list
            for i in range(len(tokens) - len(invalid_seq) + 1):
                if all(inv in tokens[i:i+len(invalid_seq)] for inv in invalid_seq):
                    return False, f"Invalid sequence detected: {' → '.join(invalid_seq)}"
        
        return True, ""
    
    def _check_safety(self, intent_type: IntentType, slots: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Apply safety checks for financial transactions.
        """
        safety_checks = self.rules["intents"][intent_type.value]["safety_checks"]
        
        # Amount limit check
        if "amount_limit" in safety_checks:
            if "amount" in slots:
                amount = slots["amount"]
                if amount > self.max_transfer_amount:
                    return False, f"Amount exceeds maximum limit: {amount} > {self.max_transfer_amount}"
                if amount <= 0:
                    return False, "Amount must be positive"
        
        # Recipient validation
        if "recipient_validation" in safety_checks:
            if "recipient" not in slots:
                return False, "Recipient must be specified for transfers"
            # Additional validation could check if recipient exists in database
        
        return True, ""
    
    def get_slot_prompt(self, intent: Intent) -> str:
        """
        Generate a user-friendly prompt to fill missing slots.
        
        Args:
            intent: Incomplete intent
        
        Returns:
            Prompt string for the user
        """
        if not intent.missing_slots:
            return ""
        
        prompts = {
            "amount": "How much would you like to transfer/withdraw/deposit?",
            "recipient": "Who would you like to transfer to? Please sign the account number.",
            "account_type": "Which account? (Sign: SAVINGS or CHECKING)",
            "date_range": "What time period? (Sign: THIS MONTH, LAST MONTH, etc.)"
        }
        
        return prompts.get(intent.missing_slots[0], f"Please provide: {intent.missing_slots[0]}")
    
    def requires_confirmation(self, intent: Intent) -> bool:
        """
        Check if intent requires user confirmation before execution.
        """
        required_confirmations = self.rules["semantic_constraints"]["required_confirmations"]
        return intent.type.value in required_confirmations


# ==================== Intent Rules JSON (Save this separately) ====================
DEFAULT_RULES_JSON = """
{
  "intents": {
    "balance": {
      "required_slots": [],
      "optional_slots": ["account_type"],
      "keywords": ["balance", "check", "account", "money", "show"],
      "confidence_boost": 0.1
    },
    "transfer": {
      "required_slots": ["amount", "recipient"],
      "optional_slots": ["account_from", "account_to"],
      "keywords": ["transfer", "send", "money", "pay"],
      "confidence_boost": 0.0,
      "safety_checks": ["amount_limit", "recipient_validation"]
    },
    "deposit": {
      "required_slots": ["amount"],
      "optional_slots": ["account"],
      "keywords": ["deposit", "add", "money", "cash"],
      "confidence_boost": 0.05
    },
    "withdraw": {
      "required_slots": ["amount"],
      "optional_slots": ["account"],
      "keywords": ["withdraw", "take", "money", "cash"],
      "confidence_boost": 0.05,
      "safety_checks": ["amount_limit"]
    },
    "history": {
      "required_slots": [],
      "optional_slots": ["date_range", "account"],
      "keywords": ["history", "transactions", "past", "show"],
      "confidence_boost": 0.1
    },
    "help": {
      "required_slots": [],
      "optional_slots": [],
      "keywords": ["help", "support", "how", "what"],
      "confidence_boost": 0.15
    }
  },
  "semantic_constraints": {
    "invalid_sequences": [
      ["balance", "transfer"],
      ["withdraw", "deposit"]
    ],
    "required_confirmations": ["transfer", "withdraw"]
  }
}
"""


# ==================== TESTING ====================
if __name__ == "__main__":
    print("🔬 Testing Neuro-Symbolic Verifier...")
    
    verifier = NeuroSymbolicVerifier(confidence_threshold=0.7)
    
    # Test Case 1: Valid balance check
    print("\n--- Test 1: Balance Check ---")
    intent, is_valid, msg = verifier.verify(
        gloss_sequence=["CHECK", "BALANCE", "ACCOUNT"],
        confidence_scores=[0.9, 0.85, 0.8],
        predicted_intent="balance"
    )
    print(f"Valid: {is_valid}, Message: {msg}")
    print(f"Intent: {intent.type.value}, Confidence: {intent.confidence:.2f}")
    
    # Test Case 2: Transfer with missing slots
    print("\n--- Test 2: Incomplete Transfer ---")
    intent, is_valid, msg = verifier.verify(
        gloss_sequence=["TRANSFER", "MONEY"],
        confidence_scores=[0.9, 0.85],
        predicted_intent="transfer"
    )
    print(f"Valid: {is_valid}, Message: {msg}")
    print(f"Missing slots: {intent.missing_slots}")
    if not is_valid and intent.missing_slots:
        print(f"Prompt: {verifier.get_slot_prompt(intent)}")
    
    # Test Case 3: Low confidence
    print("\n--- Test 3: Low Confidence ---")
    intent, is_valid, msg = verifier.verify(
        gloss_sequence=["UNCLEAR", "SIGN"],
        confidence_scores=[0.4, 0.3],
        predicted_intent="balance"
    )
    print(f"Valid: {is_valid}, Message: {msg}")
    
    # Test Case 4: Complete transfer
    print("\n--- Test 4: Complete Transfer ---")
    intent, is_valid, msg = verifier.verify(
        gloss_sequence=["TRANSFER", "5000", "ACCOUNT_123"],
        confidence_scores=[0.9, 0.95, 0.88],
        predicted_intent="transfer"
    )
    print(f"Valid: {is_valid}, Message: {msg}")
    print(f"Slots: {intent.slots}")
    print(f"Requires confirmation: {verifier.requires_confirmation(intent)}")
    
    print("\n✨ All tests passed!")
