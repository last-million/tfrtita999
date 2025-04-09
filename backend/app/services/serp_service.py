import logging
import aiohttp
import json
import os
from typing import Dict, List, Any, Optional
from ..config import settings

logger = logging.getLogger(__name__)

class SerpService:
    """
    Service to handle Search Engine Results Page (SERP) API calls
    to provide internet search capabilities to the AI.
    """
    
    def __init__(self):
        # Get API key from settings or environment variables
        self.api_key = settings.serp_api_key
        self.is_configured = self.api_key and self.api_key != "placeholder-value"
        
        # SerpAPI endpoint
        self.base_url = "https://serpapi.com/search"
        
        # Google Search endpoint (alternative)
        self.google_search_url = "https://customsearch.googleapis.com/customsearch/v1"
        self.google_cx = settings.google_search_cx
        self.using_google = settings.use_google_search or False
        
        if not self.is_configured:
            logger.warning("SERP API key is not configured. Internet search will not work.")
    
    async def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Search the internet for a given query
        
        Args:
            query: Search query
            num_results: Number of results to return (default: 5)
            
        Returns:
            Dictionary with search results
        """
        if not self.is_configured:
            logger.error("SERP API is not configured")
            return {
                "success": False,
                "error": "SERP API is not configured. Please add API key to settings.",
                "results": []
            }
        
        try:
            if self.using_google:
                return await self._google_search(query, num_results)
            else:
                return await self._serpapi_search(query, num_results)
        except Exception as e:
            logger.error(f"Error performing SERP search: {str(e)}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "results": []
            }
    
    async def _serpapi_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """
        Perform search using SerpAPI
        """
        params = {
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
            "engine": "google"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract organic results
                    organic_results = data.get("organic_results", [])
                    results = []
                    
                    for result in organic_results[:num_results]:
                        results.append({
                            "title": result.get("title", ""),
                            "link": result.get("link", ""),
                            "snippet": result.get("snippet", ""),
                            "source": "SerpAPI"
                        })
                    
                    return {
                        "success": True,
                        "query": query,
                        "results": results
                    }
                else:
                    error_msg = await response.text()
                    logger.error(f"SerpAPI error: {error_msg}")
                    return {
                        "success": False,
                        "error": f"SerpAPI error: {response.status}",
                        "results": []
                    }
    
    async def _google_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """
        Perform search using Google Custom Search API
        """
        params = {
            "q": query,
            "key": self.api_key,
            "cx": self.google_cx,
            "num": min(num_results, 10)  # Google API max is 10
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.google_search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract items from Google API
                    items = data.get("items", [])
                    results = []
                    
                    for item in items:
                        results.append({
                            "title": item.get("title", ""),
                            "link": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "Google"
                        })
                    
                    return {
                        "success": True,
                        "query": query,
                        "results": results
                    }
                else:
                    error_msg = await response.text()
                    logger.error(f"Google Search API error: {error_msg}")
                    return {
                        "success": False,
                        "error": f"Google Search API error: {response.status}",
                        "results": []
                    }
    
    async def get_weather(self, location: str) -> Dict[str, Any]:
        """
        Get weather information for a location by searching
        
        Args:
            location: Location to get weather for
            
        Returns:
            Dictionary with weather information
        """
        # Search for weather in the location
        query = f"weather in {location}"
        results = await self.search(query, 3)
        
        if not results.get("success", False):
            return {
                "success": False,
                "error": results.get("error", "Failed to get weather information"),
                "location": location
            }
        
        try:
            # Extract weather information from search results - this is a simple extraction
            # For production, you would want to use a dedicated weather API
            weather_info = {
                "location": location,
                "success": True,
                "source": "Search results",
                "temperature": None,
                "condition": None,
                "details": results.get("results", [])[0].get("snippet", "No information available")
            }
            
            return weather_info
        except Exception as e:
            logger.error(f"Error extracting weather information: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to extract weather information: {str(e)}",
                "location": location
            }
    
    async def get_news(self, topic: str = "today", num_results: int = 5) -> Dict[str, Any]:
        """
        Get news on a topic
        
        Args:
            topic: News topic (default: "today")
            num_results: Number of news items to return
            
        Returns:
            Dictionary with news articles
        """
        query = f"news {topic}"
        results = await self.search(query, num_results)
        
        if not results.get("success", False):
            return {
                "success": False,
                "error": results.get("error", "Failed to get news"),
                "topic": topic
            }
        
        return {
            "success": True,
            "topic": topic,
            "articles": results.get("results", [])
        }
    
    def get_config_status(self) -> Dict[str, Any]:
        """
        Get configuration status
        
        Returns:
            Dictionary with configuration status
        """
        if self.using_google:
            is_configured = self.is_configured and self.google_cx and self.google_cx != "placeholder-value"
            service_type = "Google Custom Search"
        else:
            is_configured = self.is_configured
            service_type = "SerpAPI"
            
        return {
            "is_configured": is_configured,
            "service_type": service_type,
            "using_google": self.using_google
        }

# Create singleton instance
serp_service = SerpService()
