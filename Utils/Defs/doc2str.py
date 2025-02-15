from Utils.Defs.pprint import pprint

def docs2str(docs, title="Document"):
    """Useful utility for making chunks into context string. Optional, but useful"""
    out_str = ""
    for doc in docs:
        doc_name = getattr(doc, 'metadata', {}).get('Title', title)
        if doc_name:
            #out_str += f"[Quote from {doc_name}] "
            out_str += f"[Quote from user chat history] "
        out_str += getattr(doc, 'page_content', str(doc)) + "\n"
    return out_str
