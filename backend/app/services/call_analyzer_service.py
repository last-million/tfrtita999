import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
from ..database import db
from ..config import settings
from .ultravox_service import ultravox_service

logger = logging.getLogger(__name__)

class CallAnalyzerService:
    """
    Service for analyzing call transcripts and extracting structured information.
    """
    
    async def analyze_call(self, call_sid: str, force_refresh: bool = False) -> Dict:
        """
        Analyze a call transcript and extract structured information.
        
        Args:
            call_sid: The call SID to analyze
            force_refresh: Whether to force reanalysis even if already exists
            
        Returns:
            Analysis results
        """
        # Check if analysis already exists and we're not forcing refresh
        if not force_refresh:
            existing = await self.get_call_analysis(call_sid)
            if existing and not "error" in existing:
                logger.info(f"Using existing analysis for call {call_sid}")
                return {"success": True, "analysis": existing}
        
        logger.info(f"Analyzing call {call_sid}")
        
        # Get call transcript from Ultravox service
        transcript = await ultravox_service.get_transcript(call_sid)
        if not transcript:
            logger.error(f"No transcript found for call {call_sid}")
            return {"success": False, "error": "No transcript found for this call"}
            
        # Extract conversation text for analysis
        conversation_text = "\n".join([f"{msg['role']}: {msg['text']}" for msg in transcript])
            
        # Extract key entities
        entities = await self._extract_entities(conversation_text)
        
        # Extract intent
        intent = await self._extract_intent(conversation_text)
        
        # Extract sentiment
        sentiment = await self._analyze_sentiment(conversation_text)
        
        # Generate summary
        summary = await self._generate_summary(conversation_text)
        
        # Extract prices mentioned
        prices = await self._extract_prices(conversation_text)
        
        # Extract follow-up actions
        follow_ups = await self._extract_follow_ups(conversation_text)
        
        # Construct analysis object
        analysis = {
            "summary": summary,
            "intent": intent,
            "entities": entities,
            "sentiment": sentiment,
            "prices": prices,
            "follow_ups": follow_ups,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        # Save analysis to database
        await self._save_analysis(call_sid, analysis)
        
        return {"success": True, "analysis": analysis}
        
    async def get_call_analysis(self, call_sid: str) -> Optional[Dict]:
        """
        Get existing call analysis from database.
        
        Args:
            call_sid: Call SID
            
        Returns:
            Analysis results or None if not found
        """
        try:
            query = "SELECT analysis FROM call_analysis WHERE call_sid = %s"
            result = await db.fetch_one(query, (call_sid,))
            
            if result and result["analysis"]:
                return json.loads(result["analysis"])
            return None
        except Exception as e:
            logger.error(f"Error retrieving call analysis: {str(e)}")
            return {"error": f"Error retrieving analysis: {str(e)}"}
            
    async def _save_analysis(self, call_sid: str, analysis: Dict) -> bool:
        """
        Save call analysis to database.
        
        Args:
            call_sid: Call SID
            analysis: Analysis data
            
        Returns:
            Success status
        """
        try:
            query = """
                INSERT INTO call_analysis (call_sid, analysis, created_at)
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                analysis = %s, updated_at = NOW()
            """
            
            await db.execute(query, (call_sid, json.dumps(analysis), json.dumps(analysis)))
            return True
        except Exception as e:
            logger.error(f"Error saving call analysis: {str(e)}")
            return False
            
    async def _extract_entities(self, text: str) -> Dict:
        """
        Extract entities from conversation text.
        
        Args:
            text: Conversation text
            
        Returns:
            Extracted entities
        """
        entities = {
            "order_numbers": [],
            "product_names": [],
            "contact_info": {
                "email": [],
                "phone": [],
                "address": []
            }
        }
        
        # Extract order numbers (typically in format #XXX-XXX or similar)
        order_pattern = r'(?:order|ticket|reference)(?:\s+number)?[\s#:]+([A-Z0-9]{5,})'
        order_matches = re.finditer(order_pattern, text, re.IGNORECASE)
        for match in order_matches:
            if match.group(1) not in entities["order_numbers"]:
                entities["order_numbers"].append(match.group(1))
        
        # Basic product name extraction - could be enhanced with named entity recognition
        product_patterns = [
            r'(?:ordered|purchased|bought|item)(?:\s+a|\s+an|\s+the)?(?:\s+)([A-Za-z0-9\s]{3,30})',
            r'(?:want|looking\s+for)\s+(?:a|an|the)\s+([A-Za-z0-9\s]{3,30})'
        ]
        
        for pattern in product_patterns:
            product_matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in product_matches:
                product = match.group(1).strip()
                if len(product) > 3 and product not in entities["product_names"]:
                    entities["product_names"].append(product)
        
        # Extract email addresses
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_matches = re.finditer(email_pattern, text)
        for match in email_matches:
            if match.group(0) not in entities["contact_info"]["email"]:
                entities["contact_info"]["email"].append(match.group(0))
        
        # Extract phone numbers
        phone_pattern = r'(?:\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
        phone_matches = re.finditer(phone_pattern, text)
        for match in phone_matches:
            if match.group(0) not in entities["contact_info"]["phone"]:
                entities["contact_info"]["phone"].append(match.group(0))
        
        # Extract addresses (simplified pattern)
        address_pattern = r'\d+\s+[A-Za-z0-9\s,\.]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)(?:[,\s]+[A-Za-z\s]+)?(?:[,\s]+[A-Z]{2})?(?:[,\s]+\d{5}(?:-\d{4})?)?'
        address_matches = re.finditer(address_pattern, text, re.IGNORECASE)
        for match in address_matches:
            if match.group(0) not in entities["contact_info"]["address"]:
                entities["contact_info"]["address"].append(match.group(0))
        
        return entities
        
    async def _extract_intent(self, text: str) -> Dict:
        """
        Extract primary and secondary intents from conversation.
        
        Args:
            text: Conversation text
            
        Returns:
            Intent classification
        """
        # Define common intent patterns
        intent_patterns = {
            "customer_service": [
                r'(?:speak|talk)\s+(?:to|with)\s+(?:a|an|your)?\s*(?:agent|representative|person|human|manager|supervisor)',
                r'(?:need|want)\s+(?:help|assistance|support)'
            ],
            "order_inquiry": [
                r'(?:check|track|about|update)\s+(?:my|the|an)?\s*order',
                r'(?:where|when|status)\s+(?:is|of|about)\s+(?:my|the)?\s*order',
                r'(?:has|have)\s+(?:my|the)?\s*order\s+(?:shipped|arrived|been\s+sent)'
            ],
            "product_inquiry": [
                r'(?:tell|know|wondering|like|need)\s+(?:me|to\s+know)?\s*(?:about|more\s+about)\s+(?:your|the|a|an)?\s*(?:product|item)',
                r'(?:what|how)\s+(?:is|are)\s+(?:your|the|this|that|these|those)?\s*(?:product|item|thing|stuff)'
            ],
            "technical_issue": [
                r'(?:not\s+working|broken|error|problem|issue|trouble|bug|glitch)',
                r'(?:website|app|application|software|system|device|product)\s+(?:is|has|keeps|won\'t|doesn\'t|can\'t)'
            ],
            "complaint": [
                r'(?:unhappy|disappointed|frustrated|upset|angry|annoyed|dissatisfied)',
                r'(?:this\s+is\s+unacceptable|not\s+acceptable|terrible|horrible|awful)',
                r'(?:want|would\s+like|demand|need)\s+(?:a|my|the)?\s*(?:refund|money\s+back)'
            ],
            "pricing_inquiry": [
                r'(?:how\s+much|what\s+is\s+the\s+price|price|cost|fee|discount|special\s+offer)',
                r'(?:cheaper|expensive|affordable|premium)'
            ],
            "purchase": [
                r'(?:want|would\s+like|need|interested\s+in|looking\s+to|like\s+to)\s+(?:buy|purchase|order|get)',
                r'(?:add|put)\s+(?:it|this|that|them|these|those)\s+(?:to|in|into)\s+(?:my|the)?\s*(?:cart|basket|order)'
            ],
            "return": [
                r'(?:return|send\s+back|exchange)',
                r'(?:doesn\'t|don\'t|didn\'t)\s+(?:fit|work|want|like)',
                r'(?:wrong|incorrect|damaged|defective)'
            ],
            "account_issue": [
                r'(?:can\'t|cannot|couldn\'t)\s+(?:log\s+in|sign\s+in|access\s+my\s+account)',
                r'(?:forgot|reset|change)\s+(?:my)?\s*(?:password|username|email)',
                r'(?:account|profile|settings)'
            ],
            "location_inquiry": [
                r'(?:where|location|address|directions)\s+(?:is|are|of|to)\s+(?:your|the|a|an)?\s*(?:store|shop|office|branch)',
                r'(?:hours|when|open|closed|close)'
            ]
        }
        
        # Count matches for each intent pattern
        intent_scores = {}
        for intent, patterns in intent_patterns.items():
            intent_scores[intent] = 0
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                intent_scores[intent] += len(matches)
                
        # Sort intents by score
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Format result
        result = {
            "primary": None,
            "secondary": []
        }
        
        if sorted_intents and sorted_intents[0][1] > 0:
            # Calculate confidence based on ratio to total matches
            total_matches = sum(score for _, score in sorted_intents)
            
            # Primary intent
            primary_intent, primary_score = sorted_intents[0]
            primary_confidence = primary_score / total_matches if total_matches > 0 else 0
            result["primary"] = {
                "name": primary_intent,
                "confidence": round(primary_confidence, 2)
            }
            
            # Secondary intents (up to 3)
            for intent, score in sorted_intents[1:4]:
                if score > 0:
                    confidence = score / total_matches
                    result["secondary"].append({
                        "name": intent,
                        "confidence": round(confidence, 2)
                    })
        
        return result
        
    async def _analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment in conversation text.
        
        Args:
            text: Conversation text
            
        Returns:
            Sentiment analysis
        """
        # Simple rule-based sentiment analysis
        # In a production system, we'd use a proper NLP model
        
        positive_words = [
            'good', 'great', 'excellent', 'awesome', 'amazing', 'fantastic',
            'wonderful', 'happy', 'glad', 'satisfied', 'pleased', 'thanks',
            'thank', 'helpful', 'perfect', 'love', 'best', 'appreciate'
        ]
        
        negative_words = [
            'bad', 'terrible', 'horrible', 'awful', 'poor', 'disappointing',
            'disappointed', 'unhappy', 'unsatisfied', 'upset', 'angry', 'mad',
            'frustrated', 'annoyed', 'complaint', 'issue', 'problem', 'wrong',
            'mistake', 'error', 'fail', 'hate', 'worst', 'terrible', 'refund'
        ]
        
        # Count word occurrences
        positive_count = 0
        negative_count = 0
        
        # Convert to lowercase and tokenize
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        for word in words:
            if word in positive_words:
                positive_count += 1
            elif word in negative_words:
                negative_count += 1
                
        # Calculate sentiment score (-1 to 1)
        total_count = positive_count + negative_count
        if total_count == 0:
            sentiment_score = 0  # Neutral
        else:
            sentiment_score = (positive_count - negative_count) / total_count
            
        # Determine sentiment category
        if sentiment_score >= 0.2:
            sentiment = "positive"
        elif sentiment_score <= -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
            
        return {
            "sentiment": sentiment,
            "score": round(sentiment_score, 2),
            "positive_count": positive_count,
            "negative_count": negative_count
        }
        
    async def _generate_summary(self, text: str) -> str:
        """
        Generate a summary of the conversation.
        
        Args:
            text: Conversation text
            
        Returns:
            Generated summary
        """
        # In a production system, we'd use a proper summarization model
        # For now, we'll extract key sentences
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Simple heuristic: take first sentence from user
        # and first response from agent, plus any sentences with key terms
        key_terms = ['order', 'problem', 'issue', 'need', 'help', 'question', 
                    'refund', 'return', 'purchase', 'price', 'cost', 'payment',
                    'shipping', 'delivery', 'address', 'account', 'login']
                    
        important_sentences = []
        
        # Find first user sentence
        user_started = False
        for sentence in sentences:
            if sentence.lower().startswith("user:"):
                important_sentences.append(sentence)
                user_started = True
                break
                
        # Find first agent response after user
        if user_started:
            for sentence in sentences:
                if sentence.lower().startswith("agent:"):
                    important_sentences.append(sentence)
                    break
                    
        # Add sentences with key terms (up to 3 more)
        key_sentences = []
        for sentence in sentences:
            words = re.findall(r'\b\w+\b', sentence.lower())
            if any(term in words for term in key_terms) and sentence not in important_sentences:
                key_sentences.append(sentence)
                if len(key_sentences) >= 3:
                    break
                    
        important_sentences.extend(key_sentences)
        
        # Join sentences into summary
        if important_sentences:
            summary = ' '.join(important_sentences)
            # Clean up summary
            summary = re.sub(r'(user|agent):\s*', '', summary, flags=re.IGNORECASE)
            return summary
        else:
            return "No summary available."
            
    async def _extract_prices(self, text: str) -> List[Dict]:
        """
        Extract prices mentioned in conversation.
        
        Args:
            text: Conversation text
            
        Returns:
            List of prices with context
        """
        prices = []
        
        # Look for dollar amounts
        price_pattern = r'\$\s*(\d+(?:\.\d{1,2})?)'
        matches = re.finditer(price_pattern, text)
        
        for match in matches:
            amount = float(match.group(1))
            
            # Get context (10 words before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            
            prices.append({
                "amount": amount,
                "context": context
            })
            
        return prices
        
    async def _extract_follow_ups(self, text: str) -> List[str]:
        """
        Extract follow-up actions from conversation.
        
        Args:
            text: Conversation text
            
        Returns:
            List of follow-up actions
        """
        follow_ups = []
        
        # Look for promises and commitments
        follow_up_patterns = [
            r'(?:I\'ll|we\'ll|will|going\s+to)\s+(?:send|email|call|contact|get\s+back|follow\s+up|check)\s+(?:you|on\s+that|with\s+you|to\s+you)(?:[^.!?]*)',
            r'(?:let\s+me|I\'ll|we\'ll|will)\s+(?:check|look\s+into|investigate|find\s+out|get\s+more\s+information)(?:[^.!?]*)',
            r'(?:I\'ll|we\'ll|will)\s+(?:schedule|set\s+up|arrange|organize)(?:[^.!?]*)'
        ]
        
        for pattern in follow_up_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                action = match.group(0).strip()
                # Clean up
                action = re.sub(r'^(agent|user):\s*', '', action, flags=re.IGNORECASE)
                action = action[0].upper() + action[1:]  # Capitalize first letter
                
                if action not in follow_ups:
                    follow_ups.append(action)
                    
        return follow_ups

# Singleton instance
call_analyzer_service = CallAnalyzerService()
