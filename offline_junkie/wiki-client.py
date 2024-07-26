"""
MIT License

Copyright (c) 2024 Jose Diaz Ayala

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import ollama
import requests
from bs4 import BeautifulSoup

# Base URL for the Wikipedia search
BASE_URL = "http://127.0.0.1/search"

def fetch_results(pattern, start=0):
    try:
        url = f"{BASE_URL}?pattern={pattern}&start={start}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        for item in soup.select('.results li'):
            title = item.select_one('a').text.strip()
            link = item.select_one('a')['href'].strip()
            articles.append({'title': title, 'link': link})
        
        # Check if there's a next page link
        next_page = soup.select_one('.footer a[href*=start]')
        next_page_start = int(next_page['href'].split('start=')[1].split('&')[0]) if next_page else None
        
        return articles, next_page_start
    except requests.RequestException as e:
        print(f"Error fetching results: {e}")
        return [], None

def fetch_article_content(link):
    try:
        url = f"http://127.0.0.1{link}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_div = soup.select_one('div.content')  # Adjust based on actual page structure
        return content_div.get_text(strip=True) if content_div else 'Content not found'
    except requests.RequestException as e:
        print(f"Error fetching article content: {e}")
        return 'Error fetching content'

def display_articles(articles):
    if not articles:
        print("No articles found.")
        return []
    
    print("Articles found:")
    for i, article in enumerate(articles):
        print(f"{i + 1}. Title: {article['title']}\n   Link: {article['link']}\n")
    return [article['link'] for article in articles]

def chat_with_ai(message):
    try:
        stream = ollama.chat(
            model='llama3.1',
            messages=[{'role': 'user', 'content': message}],
            stream=True,
        )
        response = ''
        for chunk in stream:
            response += chunk['message']['content']
        return response
    except Exception as e:
        print(f"Error chatting with AI: {e}")
        return "Error interacting with AI."

context = []
current_instruction = None
last_query_results = []

while True:
    user_input = input("> ")

    if user_input.startswith('/q '):
        # Prompt for instruction before processing the query
        instruction = input("Enter instruction (or press Enter to skip): ").strip()
        
        parts = user_input.split(maxsplit=1)
        if len(parts) == 2:
            pattern = parts[1]
            
            start = 0
            while True:
                articles, next_page_start = fetch_results(pattern, start=start)
                if not articles:
                    print("No more articles found.")
                    break

                last_query_results = articles
                display_articles(articles)
                
                ai_response = chat_with_ai('Choose one of the following articles:')
                print(ai_response)
                
                choice = input("\nEnter the number of the article you want to select or type 'next' for more results or 'exit' to quit: ")
                
                if choice.lower() == 'next' and next_page_start is not None:
                    start = next_page_start
                elif choice.lower() == 'exit':
                    break
                elif choice.isdigit() and 1 <= int(choice) <= len(articles):
                    selected_article = articles[int(choice) - 1]
                    selected_link = selected_article['link']
                    article_content = fetch_article_content(selected_link)
                    summary = chat_with_ai(f"Print out the content of the following article: {article_content}")
                    print("Summary:", summary)
                    # Print the URL of the article
                    print(f"Article URL: http://127.0.0.1{selected_link}")
                    # After summarizing, return to the main loop
                    break
                else:
                    print("Invalid choice. Please try again.")
        
        # Combine instruction with results if provided
        if instruction:
            instruction_message = f"Instruction: {instruction}\n\nResults: {last_query_results}"
            ai_response = chat_with_ai(instruction_message)
            print(ai_response)

    elif user_input == '/exit':
        print("Exiting.")
        break
    
    else:
        ai_response = chat_with_ai(user_input)
        print(ai_response)
