import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class PromptService:
    """
    Service to manage system prompts for both inbound and outbound calls
    """
    
    def __init__(self):
        # Default system prompts for different call types
        self.default_prompts = {
            'inbound': """
            You are a helpful AI assistant answering an inbound call. 
            Your goal is to assist the caller in a professional and courteous manner.
            Introduce yourself as an AI assistant and ask how you can help them today.
            Listen carefully to their questions or requests, and provide clear and concise responses.
            If you don't know the answer to a question, be honest about it.
            End the call politely when the conversation is complete.
            """,
            'outbound': """
            You are an AI assistant making an outbound call.
            Introduce yourself clearly, stating who you are and the purpose of your call.
            Be respectful of the person's time and keep the conversation focused.
            Listen to their responses carefully and adjust your approach accordingly.
            If they are not interested or wish to end the call, respect their decision promptly.
            Thank them for their time at the end of the call.
            """
        }
        
        # Custom system prompts can be stored and retrieved from the database
        self.custom_prompts = {}
        
    def get_system_prompt(self, call_type: str, custom_id: Optional[str] = None) -> str:
        """
        Get the appropriate system prompt for the call type
        
        Parameters:
        - call_type: 'inbound' or 'outbound'
        - custom_id: Optional ID to retrieve a custom prompt
        
        Returns:
        - The system prompt to use
        """
        if custom_id and custom_id in self.custom_prompts:
            return self.custom_prompts[custom_id]
            
        # Return default prompt for the call type, or outbound if not found
        return self.default_prompts.get(call_type, self.default_prompts['outbound'])
        
    async def load_custom_prompts_from_db(self, db):
        """
        Load custom prompts from the database
        """
        try:
            query = "SELECT id, prompt_type, content FROM system_prompts WHERE is_active = TRUE"
            results = await db.execute(query)
            
            for row in results:
                self.custom_prompts[row['id']] = row['content']
                
            logger.info(f"Loaded {len(results)} custom prompts from database")
        except Exception as e:
            logger.error(f"Error loading custom prompts: {e}")
            
    async def save_custom_prompt(self, db, prompt_type: str, content: str, name: str = "", is_active: bool = True) -> int:
        """
        Save a custom prompt to the database
        
        Returns:
        - The ID of the saved prompt
        """
        try:
            query = """
                INSERT INTO system_prompts (prompt_type, content, name, is_active, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id
            """
            result = await db.execute(query, (prompt_type, content, name, is_active))
            prompt_id = result[0]['id']
            
            # Add to memory cache
            self.custom_prompts[str(prompt_id)] = content
            
            return prompt_id
        except Exception as e:
            logger.error(f"Error saving custom prompt: {e}")
            raise e
            
    def format_prompt_with_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Format a prompt with context variables
        
        Parameters:
        - prompt: The prompt template
        - context: Dictionary of context variables to inject
        
        Returns:
        - Formatted prompt with context variables replaced
        """
        formatted_prompt = prompt
        
        # Replace context variables
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in formatted_prompt:
                formatted_prompt = formatted_prompt.replace(placeholder, str(value))
                
        return formatted_prompt

# Create a singleton instance
prompt_service = PromptService()
