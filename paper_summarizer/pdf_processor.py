from typing import Dict, List, Optional
import re
from pypdf import PdfReader

class PdfProcessor:
    def __init__(self, file_path: str):
        """Initialize the PDF processor with a file path."""
        self.file_path = file_path
        self.reader = PdfReader(file_path)
        self.full_text = ""
        self.sections: Dict[str, str] = {}
        
    def extract_text(self) -> str:
        """Extract text from all pages of the PDF."""
        text_parts = []
        for page in self.reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        self.full_text = "\n".join(text_parts)
        return self.full_text
    
    def identify_sections(self) -> Dict[str, str]:
        """Identify common research paper sections in the text."""
        common_sections = [
            "abstract", "introduction", "background",
            "methodology", "methods", "experimental setup", "experiment", "experiments"
            "results", "discussion", "conclusion", "conclusions",
            "references", "acknowledgments", "related work"
        ]

        section_pattern = r"(?im)^(?:\d+\.?\d*\s*|[IVXivx]+\.?\s*)?({})(?:\s*:|$)".format(
            "|".join(common_sections)
        )
        
        lines = self.full_text.split('\n')
        current_section = "unknown"
        current_content = []
        
        for i, line in enumerate(lines):
            match = re.search(section_pattern, line.strip(), re.IGNORECASE)
            
            is_section_header = False
            if match:
                is_section_header = True
            else:
                if line.strip().isupper() and any(section in line.lower() for section in common_sections):
                    match = re.search(r"(?i)(" + "|".join(common_sections) + r")", line)
                    is_section_header = bool(match)
            
            if is_section_header and match: #Section header is found
                if current_content:
                    self.sections[current_section] = "\n".join(current_content).strip() #Savign previous section and ccontinuing
                    current_content = []
                
                current_section = match.group(1).lower()
                continue
            
            current_content.append(line)
        
        if current_content:
            self.sections[current_section] = "\n".join(current_content).strip() #Saving last section
        
        # If we only found unknown sections, try alternative approach
        if len(self.sections) <= 2:  # only unknown and maybe references
            self._try_alternative_section_detection()
        
        return self.sections
    
    def _try_alternative_section_detection(self):
        """Alternative approach to detect sections using typography hints."""
        lines = self.full_text.split('\n')
        potential_sections = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            # Characteristics of likely headers:
            # - Relatively short
            # - Possibly all caps
            # - Might start with numbers
            # - Might be followed by blank line
            if (len(line) < 100 and  # Not too long
                (line.isupper() or  # All caps
                 re.match(r'^\d+\.?\s+[A-Z]', line) or  # Numbered sections
                 re.match(r'^[IVXivx]+\.?\s+[A-Z]', line)) and  # Roman numerals
                (i + 1 >= len(lines) or not lines[i + 1].strip())):  # Followed by blank line
                
                potential_sections.append((i, line))
        
        # Process identified potential sections
        if potential_sections:
            new_sections = {}
            for idx, (line_num, header) in enumerate(potential_sections):
                # Get content until next section or end
                next_line = potential_sections[idx + 1][0] if idx + 1 < len(potential_sections) else len(lines)
                content = "\n".join(lines[line_num + 1:next_line]).strip()
                
                # Clean up header
                clean_header = re.sub(r'^\d+\.?\s*|^[IVXivx]+\.?\s*', '', header.lower())
                new_sections[clean_header] = content
            
            if len(new_sections) > len(self.sections):
                self.sections = new_sections
    
    def get_section(self, section_name: str) -> Optional[str]:
        """Get the content of a specific section."""
        return self.sections.get(section_name.lower())
    
    def get_metadata(self) -> Dict[str, str]:
        """Extract metadata from the PDF."""
        metadata = {}
        pdf_info = self.reader.metadata
        
        if pdf_info:
            for key in ["/Title", "/Author", "/CreationDate"]:
                value = pdf_info.get(key, "")
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8')
                    except UnicodeDecodeError:
                        value = str(value)
                metadata[key.lower().strip('/')] = str(value)
            
        if not metadata.get("title"):
            try:
                first_page_text = self.reader.pages[0].extract_text()
                lines = [l.strip() for l in first_page_text.split('\n') if l.strip()]
                if lines:
                    metadata["title"] = lines[0]
            except:
                pass
                
        return metadata

    def process(self) -> Dict[str, str]:
        """Process the PDF and return all extracted information."""
        self.extract_text()
        sections = self.identify_sections()
        metadata = self.get_metadata()
        
        return {
            "metadata": metadata,
            "sections": sections,
            "full_text": self.full_text
        }