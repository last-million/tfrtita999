import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    """
    A service that analyzes call transcripts to extract relevant information
    such as names, emails, phone numbers, and other contact details.
    """
    
    def __init__(self):
        # Set up regular expressions for common patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'\b(\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'
        self.name_patterns = [
            r'(?:my name is|I am|I\'m|this is) ([A-Z][a-z]+ [A-Z][a-z]+)',
            r'(?:my name is|I am|I\'m|this is) ([A-Z][a-z]+)',
            r'(?:call me|I\'m called) ([A-Z][a-z]+)'
        ]
        self.company_patterns = [
            r'(?:I work for|I\'m with|I\'m from|I represent|I\'m calling from) ([A-Z][A-Za-z0-9\s&.\-]+)',
            r'(?:my company is|my company\'s name is) ([A-Z][A-Za-z0-9\s&.\-]+)'
        ]
        self.address_patterns = [
            r'\b\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way)\b'
        ]

    def extract_client_info(self, transcription: str) -> Dict[str, Any]:
        """
        Extract client information from a call transcription
        """
        if not transcription:
            return {}
            
        result = {}
        
        # Extract email
        email = self._extract_email(transcription)
        if email:
            result['email'] = email
            
        # Extract phone
        phone = self._extract_phone(transcription)
        if phone:
            result['phone'] = phone
            
        # Extract name
        name = self._extract_name(transcription)
        if name:
            result['name'] = name
            
        # Extract company
        company = self._extract_company(transcription)
        if company:
            result['company'] = company
            
        # Extract address
        address = self._extract_address(transcription)
        if address:
            result['address'] = address
            
        return result
        
    def enhance_client_data(self, client_data: Dict[str, Any], transcription: str) -> Dict[str, Any]:
        """
        Enhance client data with information extracted from transcription
        """
        if not transcription:
            return client_data
            
        # Create a copy of the client data
        enhanced_data = client_data.copy()
        
        # Extract client info
        extracted_info = self.extract_client_info(transcription)
        
        # Fill in missing fields
        for field, value in extracted_info.items():
            if field not in enhanced_data or not enhanced_data[field]:
                enhanced_data[field] = value
                
        return enhanced_data
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from text"""
        email_matches = re.findall(self.email_pattern, text)
        return email_matches[0] if email_matches else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        phone_matches = re.findall(self.phone_pattern, text)
        return phone_matches[0] if phone_matches else None
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name from text"""
        for pattern in self.name_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None
    
    def _extract_company(self, text: str) -> Optional[str]:
        """Extract company name from text"""
        for pattern in self.company_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address from text"""
        for pattern in self.address_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None
    
    def process_call_data(self, call_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process call data to enhance client information based on transcriptions
        """
        processed_data = []
        
        for call in call_data:
            # Skip calls without transcription
            if not call.get('transcription'):
                processed_data.append(call)
                continue
                
            # Enhance client data with info from transcription
            transcription = call.get('transcription', '')
            
            # Create a client_info field if not exists
            if 'client_info' not in call:
                call['client_info'] = {}
                
            # Enhance client info
            call['client_info'] = self.enhance_client_data(call.get('client_info', {}), transcription)
            
            processed_data.append(call)
            
        return processed_data
