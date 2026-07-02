#!/usr/bin/env python3
"""
🎭 Random Joke Generator
A utility to fetch and display random jokes from an external API.
Perfect for taking a break during infrastructure tasks! 😄

Uses the JokeAPI (https://jokeapi.dev/) for diverse joke content.
"""

import requests
import sys
import argparse
import json
from typing import Optional, Dict, Any
from datetime import datetime

# Configuration
JOKE_API_URL = "https://v2.jokeapi.dev/joke/"
DEFAULT_JOKE_TYPE = "Any"
AVAILABLE_TYPES = ["General", "Programming", "Knock-knock", "Any"]
SAFE_MODE = True

class JokeGenerator:
    """Fetches and manages random jokes from external API."""
    
    def __init__(self, safe_mode: bool = True, timeout: int = 10):
        """
        Initialize the Joke Generator.
        
        Args:
            safe_mode (bool): Filter for family-friendly content
            timeout (int): Request timeout in seconds
        """
        self.safe_mode = safe_mode
        self.timeout = timeout
        self.last_joke = None
    
    def fetch_joke(self, joke_type: str = "Any") -> Optional[Dict[str, Any]]:
        """
        Fetch a random joke from the API.
        
        Args:
            joke_type (str): Type of joke (General, Programming, Knock-knock, Any)
            
        Returns:
            Dict containing joke data or None if request fails
        """
        if joke_type not in AVAILABLE_TYPES:
            print(f"❌ Invalid joke type. Available: {', '.join(AVAILABLE_TYPES)}")
            return None
        
        try:
            url = f"{JOKE_API_URL}{joke_type}"
            params = {
                "safe-mode": self.safe_mode,
                "format": "json"
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            joke_data = response.json()
            
            if joke_data.get("error"):
                print(f"❌ API Error: {joke_data.get('message')}")
                return None
            
            self.last_joke = joke_data
            return joke_data
            
        except requests.exceptions.Timeout:
            print("❌ Request timeout. Check your internet connection.")
            return None
        except requests.exceptions.ConnectionError:
            print("❌ Connection error. Unable to reach the joke API.")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return None
    
    def display_joke(self, joke_data: Dict[str, Any], format_type: str = "text") -> None:
        """
        Display the joke in specified format.
        
        Args:
            joke_data (Dict): Joke data from API
            format_type (str): Output format (text, json, verbose)
        """
        if not joke_data:
            print("❌ No joke data to display.")
            return
        
        if format_type == "json":
            print(json.dumps(joke_data, indent=2))
        elif format_type == "verbose":
            self._display_verbose(joke_data)
        else:
            self._display_text(joke_data)
    
    def _display_text(self, joke_data: Dict[str, Any]) -> None:
        """Display joke in simple text format."""
        joke_type = joke_data.get("type", "unknown")
        category = joke_data.get("category", "Unknown")
        
        print(f"\n{'='*60}")
        print(f"📂 Category: {category}")
        print(f"{'='*60}")
        
        if joke_type == "single":
            print(f"\n😄 {joke_data.get('joke', 'No joke text')}\n")
        elif joke_type == "twopart":
            print(f"\n🎤 Setup: {joke_data.get('setup', '')}")
            print(f"⏱️  Punchline: {joke_data.get('delivery', '')}\n")
        else:
            print(f"\n⚠️  Unknown joke type\n")
        
        print(f"{'='*60}\n")
    
    def _display_verbose(self, joke_data: Dict[str, Any]) -> None:
        """Display joke with detailed metadata."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n{'='*60}")
        print(f"📊 JOKE DETAILS - {timestamp}")
        print(f"{'='*60}")
        print(f"Category:     {joke_data.get('category', 'N/A')}")
        print(f"Type:         {joke_data.get('type', 'N/A')}")
        print(f"Safe Mode:    {'Yes' if joke_data.get('safe', False) else 'No'}")
        print(f"Flags:        {joke_data.get('flags', {})}")
        print(f"{'='*60}")
        
        joke_type = joke_data.get("type", "unknown")
        if joke_type == "single":
            print(f"\n{joke_data.get('joke', 'No joke text')}\n")
        elif joke_type == "twopart":
            print(f"\nSetup: {joke_data.get('setup', '')}")
            print(f"Punchline: {joke_data.get('delivery', '')}\n")
        
        print(f"{'='*60}\n")
    
    def save_joke(self, filepath: str = "joke.json") -> bool:
        """
        Save the last fetched joke to a JSON file.
        
        Args:
            filepath (str): Path where to save the joke
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.last_joke:
            print("❌ No joke to save. Fetch one first!")
            return False
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.last_joke, f, indent=2, ensure_ascii=False)
            print(f"✅ Joke saved to: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Failed to save joke: {str(e)}")
            return False


def main():
    """Main entry point for the joke generator CLI."""
    parser = argparse.ArgumentParser(
        description="🎭 Random Joke Generator - Fetch jokes from an external API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Get a random joke
  %(prog)s -t Programming               # Get a programming joke
  %(prog)s -t Any -f json               # Output as JSON
  %(prog)s -t General -f verbose        # Detailed output
  %(prog)s -t Knock-knock -s            # Save the joke to file
        """
    )
    
    parser.add_argument(
        '-t', '--type',
        choices=AVAILABLE_TYPES,
        default=DEFAULT_JOKE_TYPE,
        help=f'Joke type (default: {DEFAULT_JOKE_TYPE})'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['text', 'json', 'verbose'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '-s', '--save',
        action='store_true',
        help='Save the joke to a JSON file'
    )
    
    parser.add_argument(
        '-u', '--unsafe',
        action='store_true',
        help='Disable safe mode (allows explicit content)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Request timeout in seconds (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = JokeGenerator(
        safe_mode=not args.unsafe,
        timeout=args.timeout
    )
    
    # Fetch joke
    print("🔄 Fetching a random joke...")
    joke_data = generator.fetch_joke(args.type)
    
    if not joke_data:
        sys.exit(1)
    
    # Display joke
    generator.display_joke(joke_data, format_type=args.format)
    
    # Save if requested
    if args.save:
        generator.save_joke()


if __name__ == "__main__":
    main()
