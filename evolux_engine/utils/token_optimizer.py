import tiktoken
from typing import List, Dict, Optional

class TokenOptimizer:
    """
    A utility class for managing and optimizing token usage in LLM prompts.
    """
    def __init__(self, model_name: str = "gpt-4"):
        try:
            self.encoder = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Counts the number of tokens in a given text."""
        return len(self.encoder.encode(text))

    def truncate_messages(self, messages: List[Dict[str, str]], max_tokens: int) -> List[Dict[str, str]]:
        """
        Truncates a list of messages to fit within a specified token limit,
        prioritizing more recent messages.
        """
        total_tokens = sum(self.count_tokens(msg["content"]) for msg in messages)
        if total_tokens <= max_tokens:
            return messages

        truncated_messages = []
        current_tokens = 0
        
        # Always include the last message
        last_message = messages[-1]
        last_message_tokens = self.count_tokens(last_message["content"])
        
        if last_message_tokens > max_tokens:
            # If the last message alone exceeds the limit, truncate it
            truncated_content = self.encoder.decode(self.encoder.encode(last_message["content"])[:max_tokens])
            truncated_messages.append({"role": last_message["role"], "content": truncated_content})
            return truncated_messages

        truncated_messages.append(last_message)
        current_tokens += last_message_tokens

        # Add previous messages until the token limit is reached
        for msg in reversed(messages[:-1]):
            msg_tokens = self.count_tokens(msg["content"])
            if current_tokens + msg_tokens <= max_tokens:
                truncated_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        return truncated_messages
