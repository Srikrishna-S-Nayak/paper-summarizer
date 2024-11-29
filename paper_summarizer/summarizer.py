from typing import Dict, Optional
import json
import requests

class PaperSummarizer:
    def __init__(self, model: str = "mistral", host: str = "http://localhost:11434"):
        """Initialize the summarizer with Ollama configuration."""
        self.model = model
        self.host = host
        self.api_endpoint = f"{host}/api/generate"
    
    def _generate_summary(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate summary using Ollama API."""
        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens
                    }
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return ""

    def summarize_section(self, section_text: str, section_name: str) -> str:
        """Summarize a specific section of the paper."""
        if not section_text:
            return ""
            
        prompt = f"""Summarize the following {section_name} section of a research paper.
        Focus on the key points and maintain academic language.
        Keep the summary concise but informative.

        {section_text}

        Summary:"""
        
        return self._generate_summary(prompt)

    def generate_full_summary(self, paper_content: Dict[str, str]) -> Dict[str, str]:
        """Generate structured summary for the entire paper."""
        summaries = {}
        sections = paper_content.get("sections", {})
        
        for section_name, content in sections.items():
            if section_name.lower() not in ["unknown", "references", "acknowledgments"]:
                summary = self.summarize_section(content, section_name)
                if summary:
                    summaries[section_name] = summary
        
        if "abstract" in sections:
            main_text = sections["abstract"]
        else:
            main_text = paper_content.get("full_text", "")[:1000]  # First 1000 chars if no abstract
            
        overall_prompt = f"""Create a brief overview of this research paper.
        Focus on the main contributions and findings.

        {main_text}

        Overview:"""
        
        summaries["overview"] = self._generate_summary(overall_prompt)
        
        return summaries

    def format_summary_markdown(self, paper_content: Dict[str, str], 
                              summaries: Dict[str, str]) -> str:
        """Format the summary in Markdown."""
        metadata = paper_content.get("metadata", {})
        
        md_parts = [
            "# Paper Summary\n",
            f"## Metadata\n",
            f"- Title: {metadata.get('title', 'N/A')}\n",
            f"- Author(s): {metadata.get('author', 'N/A')}\n\n",
            f"## Overview\n{summaries.get('overview', '')}\n"
        ]
        
        for section, summary in summaries.items():
            if section != "overview":
                md_parts.append(f"## {section.title()}\n{summary}\n")
        
        return "\n".join(md_parts)