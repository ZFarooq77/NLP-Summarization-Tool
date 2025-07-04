import requests
from bs4 import BeautifulSoup
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

#punkt: used to split text into sentences/words
#stopwords: a list of common English words to ignore (like "the", "is")
nltk.download('punkt')
nltk.download('stopwords')

BASE_URL = "https://books.toscrape.com/"


#Summarizes long text by picking the most "important" sentence(s).
def summarize(text, max_sentences=1):
    if not text:
        return ""
    
    stop_words = set(stopwords.words("english"))
    words = word_tokenize(text.lower())
    words = [w for w in words if w.isalpha() and w not in stop_words]

    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1

    sentence_scores = {}
    for sent in sent_tokenize(text):
        score = sum(freq.get(word, 0) for word in word_tokenize(sent.lower()))
        sentence_scores[sent] = score

    top_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_sentences]
    return " ".join(top_sentences)


#Sends a GET request to the book listing page.
#Parses the HTML using BeautifulSoup.
def get_book_links(page_url):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, "html.parser")
    #Finds all <a> tags for books and builds full URLs.
    links = [BASE_URL + "catalogue/" + a['href'].replace('../../../', '') 
             for a in soup.select("article.product_pod h3 a")]
    #Returns the list of book links and the pagination next button (to go to next page).
    return links, soup.select_one("li.next a")

#Sends request to individual book page and parses it.
def get_book_details(book_url):
    response = requests.get(book_url)
    soup = BeautifulSoup(response.content, "html.parser")

    #Extracts the title, price, and availability.
    title = soup.select_one("div.product_main h1").text.strip()
    price = soup.select_one("p.price_color").text.strip()
    availability = soup.select_one("p.availability").text.strip()

    # Finds the description paragraph after the #product_description heading.
    desc_tag = soup.select_one("#product_description ~ p")
    description = desc_tag.text.strip() if desc_tag else ""

    #Returns a dictionary of book info and a summary of the description.
    return {
        "title": title,
        "price": price,
        "availability": availability,
        "description": description,
        "summary of desc": summarize(description)
    }

#Starts at page 1 and prepares to loop through all pages.
def scrape_all_books():
    books_data = []
    next_url = BASE_URL + "catalogue/page-1.html"

    #While there's a next page, keep scraping and collecting links.
    while next_url:
        print(f"Scraping page: {next_url}")
        links, next_btn = get_book_links(next_url)

        #For each book link, get its data and save it. If something fails, it logs the error but continues.
        for link in links:
            print(f"→ {link}")
            try:
                book_data = get_book_details(link)
                books_data.append(book_data)
            except Exception as e:
                print(f"Error scraping {link}: {e}")

        #Checks for a next page and prepares the next URL — else, stops the loop.
        if next_btn:
            href = next_btn['href']
            next_url = BASE_URL + "catalogue/" + href
        else:
            next_url = None

    return books_data

if __name__ == "__main__":
    all_books = scrape_all_books()
    df = pd.DataFrame(all_books)
    df.to_csv("books_summary.csv", index=False, encoding='utf-8')
    print("\n✅ Done! Data saved to books_summary.csv")
