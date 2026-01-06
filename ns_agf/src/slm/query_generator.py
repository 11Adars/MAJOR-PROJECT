"""
Small Language Model (SLM) Query Generator
Uses Phi-3 Mini / TinyLlama for natural language query generation from sign keywords
"""

import os
import time
from ctransformers import AutoModelForCausalLM

class QueryGenerator:
    """Generate natural language queries from sign keywords using SLM"""
    
    def __init__(self, use_slm=True, cache_path="../Sign/slm_model_cache"):
        """
        Initialize QueryGenerator
        
        Args:
            use_slm: Whether to use SLM for generation
            cache_path: Path to cached SLM model
        """
        self.use_slm = use_slm
        self.slm_model = None
        self.cache_path = cache_path
        
        if use_slm:
            self._load_slm_model()
    
    def _load_slm_model(self):
        """Load the TinyLlama SLM model"""
        try:
            print("🔄 Loading SLM (Small Language Model)...")
            
            # Model configuration
            model_name = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
            model_file = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
            
            # Create cache directory if needed
            if not os.path.exists(self.cache_path):
                os.makedirs(self.cache_path)
            
            # Load model using ctransformers
            self.slm_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                model_file=model_file,
                model_type="llama",
                local_files_only=False,
                gpu_layers=0  # Set to 50+ if you have a GPU
            )
            
            print("✅ SLM loaded successfully!")
            return True
            
        except Exception as e:
            print(f"⚠️ Error loading SLM: {e}")
            print("⚠️ SLM will be disabled - using fallback queries")
            self.slm_model = None
            self.use_slm = False
            return False
    
    def generate_query(self, sign_name, intent=None, hand_landmarks=None):
        """
        Generate a natural language query from sign information
        
        Args:
            sign_name: Recognized sign name (e.g., "HELP", "TRANSFER")
            intent: Banking intent (e.g., "customer_support", "send_money")
            hand_landmarks: Hand landmark data (optional)
        
        Returns:
            Generated query string or fallback query
        """
        
        if not self.use_slm or not self.slm_model:
            # Return fallback query if SLM not available
            return self._get_fallback_query(sign_name, intent)
        
        try:
            # Create keywords from sign and intent
            keywords = self._extract_keywords(sign_name, intent, hand_landmarks)
            
            # Generate query using SLM
            query = self._slm_generate_sentence(keywords)
            
            return query
            
        except Exception as e:
            print(f"❌ Error generating query: {e}")
            return self._get_fallback_query(sign_name, intent)
    
    def _extract_keywords(self, sign_name, intent=None, hand_landmarks=None):
        """Extract keywords from sign information"""
        
        keywords = [sign_name]
        
        # Add intent-related keywords
        intent_keywords = {
            'customer_support': ['HELP', 'SUPPORT'],
            'send_money': ['TRANSFER', 'MONEY'],
            'check_balance': ['BALANCE', 'ACCOUNT'],
            'transaction_error': ['ERROR', 'PROBLEM'],
            'account_help': ['ACCOUNT', 'HELP'],
            'card_issue': ['CARD', 'PROBLEM'],
            'password_reset': ['PASSWORD', 'RESET'],
            'complaint': ['COMPLAINT', 'ISSUE']
        }
        
        if intent and intent in intent_keywords:
            keywords.extend(intent_keywords[intent])
        
        # Remove duplicates and return
        return list(dict.fromkeys(keywords))
    
    def _slm_generate_sentence(self, keywords):
        """
        Generate a sentence from keywords using the SLM
        
        Args:
            keywords: List of keywords
        
        Returns:
            Generated sentence
        """
        
        if not self.slm_model:
            return None
        
        # Create keyword string
        keyword_string = ", ".join(keywords)
        
        # Create few-shot prompt for TinyLlama
        system_prompt = (
            "You are a helpful banking assistant. "
            "Convert keyword lists into a single, complete banking query sentence."
        )
        
        prompt = (
            f"<|system|>\n{system_prompt}</s>\n"
            f"<|user|>\nKeywords: MY, CARD, MISSING</s>\n"
            f"<|assistant|>\nMy card is missing.</s>\n"
            f"<|user|>\nKeywords: HELP, ACCOUNT, BALANCE</s>\n"
            f"<|assistant|>\nI need help checking my account balance.</s>\n"
            f"<|user|>\nKeywords: TRANSFER, MONEY, PROBLEM</s>\n"
            f"<|assistant|>\nI have a problem transferring money.</s>\n"
            f"<|user|>\nKeywords: {keyword_string}</s>\n"
            f"<|assistant|>\n"
        )
        
        try:
            print(f"🔄 SLM generating query from keywords: {keywords}...")
            start_time = time.time()
            
            # Generate using the model
            generated_text = self.slm_model(
                prompt,
                max_new_tokens=50,
                stop=["</s>", "<|user|>"],
                temperature=0.3  # Lower temperature = more consistent output
            )
            
            elapsed = time.time() - start_time
            print(f"✅ Generated in {elapsed:.2f}s")
            
            # Clean up the generated text
            generated_text = generated_text.strip()
            
            # Remove any remaining special tokens
            generated_text = generated_text.replace("</s>", "").replace("<|user|>", "").strip()
            
            return generated_text if generated_text else None
            
        except Exception as e:
            print(f"❌ SLM generation error: {e}")
            return None
    
    def _get_fallback_query(self, sign_name, intent=None):
        """
        Generate a fallback query when SLM is unavailable
        
        Args:
            sign_name: Recognized sign name
            intent: Banking intent
        
        Returns:
            Fallback query string
        """
        
        fallback_queries = {
            'customer_support': f"Customer signed '{sign_name}' and needs assistance with banking services",
            'send_money': f"Customer signed '{sign_name}' and wants to transfer money",
            'check_balance': f"Customer signed '{sign_name}' and wants to check account balance",
            'transaction_error': f"Customer signed '{sign_name}' and reported a transaction issue",
            'account_help': f"Customer signed '{sign_name}' and needs help with their account",
            'card_issue': f"Customer signed '{sign_name}' and has a card-related problem",
            'password_reset': f"Customer signed '{sign_name}' and needs to reset their password",
            'complaint': f"Customer signed '{sign_name}' and has a complaint"
        }
        
        if intent and intent in fallback_queries:
            return fallback_queries[intent]
        else:
            return f"Customer signed '{sign_name}' and needs help with banking services"
    
    def health_check(self):
        """Check if SLM is loaded and ready"""
        return {
            'slm_available': self.slm_model is not None,
            'use_slm': self.use_slm,
            'status': 'ready' if self.slm_model else 'using_fallback'
        }
