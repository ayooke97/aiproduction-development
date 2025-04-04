import requests
import json
from typing import Dict, Any, Optional
import time

# API base URL
API_BASE_URL = "http://localhost:8000/api/v1"

def search_documents(
    query: str,
    verbosity: str = "detailed",
    format_style: str = "simple",
    citations: bool = True,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Search for legal documents using the API.
    
    Args:
        query: The search query
        verbosity: Response verbosity (concise, detailed, comprehensive)
        format_style: Response format (simple, legal, technical)
        citations: Whether to include citations
        max_results: Maximum number of results to return
        
    Returns:
        API response as a dictionary
    """
    # Create the request payload
    payload = {
        "query": query,
        "preferences": {
            "verbosity": verbosity,
            "format": format_style,
            "citations": citations,
            "max_results": max_results
        }
    }
    
    # Send the request
    response = requests.post(
        f"{API_BASE_URL}/search/query",
        json=payload
    )
    
    # Check for errors
    response.raise_for_status()
    
    # Parse the response
    data = response.json()
    
    return data

def simple_search(
    query: str,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Simple search using query parameters.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        API response as a dictionary
    """
    # Create the query parameters
    params = {
        "query": query,
        "max_results": max_results,
        "verbosity": "detailed",
        "format": "simple",
        "citations": True
    }
    
    # Send the request
    response = requests.get(
        f"{API_BASE_URL}/search/simple",
        params=params
    )
    
    # Check for errors
    response.raise_for_status()
    
    # Parse the response
    data = response.json()
    
    return data

def generate_report(
    query: str,
    verbosity: str = "detailed",
    format_style: str = "simple",
    citations: bool = True,
    max_results: int = 5,
    output_file: Optional[str] = None
) -> None:
    """
    Generate an HTML report of search results.
    
    Args:
        query: The search query
        verbosity: Response verbosity (concise, detailed, comprehensive)
        format_style: Response format (simple, legal, technical)
        citations: Whether to include citations
        max_results: Maximum number of results to return
        output_file: Output file path (or None to use auto-generated name)
    """
    # Create the request payload
    payload = {
        "query": query,
        "preferences": {
            "verbosity": verbosity,
            "format": format_style,
            "citations": citations,
            "max_results": max_results
        }
    }
    
    # Send the request
    response = requests.post(
        f"{API_BASE_URL}/search/report",
        json=payload
    )
    
    # Check for errors
    response.raise_for_status()
    
    # Save the response content to a file
    if output_file is None:
        # Generate a filename based on the query
        safe_query = query.replace(' ', '_')
        timestamp = int(time.time())
        output_file = f"legal_report_{safe_query}_{timestamp}.html"
    
    with open(output_file, "wb") as f:
        f.write(response.content)
    
    print(f"Report saved to {output_file}")

def extract_pdf_content(pdf_url: str, title: str = "PDF Document") -> Dict[str, Any]:
    """
    Extract content from a PDF file.
    
    Args:
        pdf_url: URL of the PDF file
        title: Title of the document
        
    Returns:
        API response as a dictionary
    """
    # Create the request payload
    payload = {
        "pdf_url": pdf_url,
        "title": title
    }
    
    # Send the request
    response = requests.post(
        f"{API_BASE_URL}/documents/extract-pdf",
        json=payload
    )
    
    # Check for errors
    response.raise_for_status()
    
    # Parse the response
    data = response.json()
    
    return data

def upload_pdf(pdf_file_path: str, title: str = "Uploaded PDF Document") -> Dict[str, Any]:
    """
    Upload and extract content from a PDF file.
    
    Args:
        pdf_file_path: Path to the PDF file
        title: Title of the document
        
    Returns:
        API response as a dictionary
    """
    # Open the PDF file
    with open(pdf_file_path, "rb") as f:
        files = {"file": (pdf_file_path, f, "application/pdf")}
        data = {"title": title}
        
        # Send the request
        response = requests.post(
            f"{API_BASE_URL}/documents/upload-pdf",
            files=files,
            data=data
        )
    
    # Check for errors
    response.raise_for_status()
    
    # Parse the response
    data = response.json()
    
    return data

def pretty_print_response(data: Dict[str, Any]) -> None:
    """
    Pretty print API response.
    
    Args:
        data: API response dictionary
    """
    print(json.dumps(data, indent=2, ensure_ascii=False))

def main():
    """Example usage of the BPK Legal Document API."""
    # Example 1: Search for documents
    print("Example 1: Search for documents")
    print("-" * 50)
    result = search_documents(
        query="hak tanah ulayat",
        verbosity="detailed",
        format_style="simple",
        citations=True,
        max_results=3
    )
    print(f"Found {len(result['documents'])} documents")
    print(f"Response: {result['response'][:200]}...")
    print()
    
    # Example 2: Simple search
    print("Example 2: Simple search")
    print("-" * 50)
    result = simple_search(
        query="peraturan daerah",
        max_results=2
    )
    print(f"Found {len(result['documents'])} documents")
    print(f"Response: {result['response'][:200]}...")
    print()
    
    # Example 3: Generate a report
    print("Example 3: Generate a report")
    print("-" * 50)
    generate_report(
        query="undang-undang agraria",
        verbosity="comprehensive",
        format_style="legal",
        citations=True,
        max_results=5
    )
    print()
    
    # Example 4: Extract PDF content (if you have a PDF URL)
    # pdf_url = "https://example.com/document.pdf"
    # result = extract_pdf_content(pdf_url)
    # print("Example 4: Extract PDF content")
    # print("-" * 50)
    # print(f"Title: {result['metadata']['title']}")
    # print(f"Pages: {result['metadata']['pages']}")
    # print(f"Content preview: {result['content'][:200]}...")
    # print()
    
    # Example 5: Upload PDF (if you have a local PDF file)
    # pdf_file_path = "path/to/your/document.pdf"
    # result = upload_pdf(pdf_file_path)
    # print("Example 5: Upload PDF")
    # print("-" * 50)
    # print(f"Title: {result['metadata']['title']}")
    # print(f"Pages: {result['metadata']['pages']}")
    # print(f"Content preview: {result['content'][:200]}...")

if __name__ == "__main__":
    main()