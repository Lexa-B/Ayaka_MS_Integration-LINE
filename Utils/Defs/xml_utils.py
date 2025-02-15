from xml.dom.minidom import parseString
import re

def flatten_xml(xml_string: str) -> str:
    """Flatten XML string to a single line, preserving content.
    
    Args:
        xml_string: Multi-line XML string
        
    Returns:
        Single-line XML string with preserved content
    """
    # Parse and re-serialize to normalize
    try:
        dom = parseString(xml_string)
        one_line = dom.toxml()
        
        # Clean up extra whitespace between tags
        one_line = re.sub(r'>\s+<', '><', one_line)
        # Clean up whitespace around text content
        one_line = re.sub(r'>\s+([^<])', r'>\1', one_line)
        one_line = re.sub(r'([^>])\s+<', r'\1<', one_line)
        
        return one_line
    except:
        # Fallback to basic flattening if not valid XML
        return ' '.join(line.strip() for line in xml_string.splitlines()) 