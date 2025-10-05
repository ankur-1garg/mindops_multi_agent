import os
import time
import json
import hashlib
import faiss
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from urllib.parse import urlparse
import config

class CodeMapper:
    """
    Intelligently maps a URL to a source file in a Next.js 14 project.
    """
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def find_source_file_for_url(self, url: str) -> str:
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.strip('/').split('/')
        
        # Handle the root URL case
        if path_segments == ['']:
            # The main page in your repo is src/app/(main)/page.tsx
            potential_path = os.path.join(self.repo_path, 'src', 'app', '(main)', 'page.tsx')
            if os.path.exists(potential_path):
                return os.path.relpath(potential_path, self.repo_path)
            return None

        # Try to find a matching file path based on URL segments
        # e.g., /agency/sign-up -> src/app/agency/sign-up/page.tsx
        potential_path = os.path.join(self.repo_path, 'src', 'app', *path_segments, 'page.tsx')
        
        if os.path.exists(potential_path):
            return os.path.relpath(potential_path, self.repo_path)
        
        # Fallback for dynamic routes or other structures if needed
        # For now, we return None if a direct match isn't found
        print(f"  -> Warning: No direct file match found for URL {url}. Defaulting to main page.")
        main_page_path = os.path.join(self.repo_path, 'src', 'app', '(main)', 'page.tsx')
        return os.path.relpath(main_page_path, self.repo_path)


class CatalogBuilder:
    """
    Crawls a web app, generates descriptions, maps code, and builds an index.
    """
    def __init__(self, app_url: str, repo_path: str):
        self.app_url = app_url
        self.code_mapper = CodeMapper(repo_path) # Use the intelligent mapper
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.llm = genai.GenerativeModel('gemini-1.5-pro')

    # ... (crawl_app and generate_ai_descriptions methods are unchanged)
    def crawl_app(self):
        """Crawls the web application to discover all unique screens."""
        print("🕷️  Starting web crawler...")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        to_visit = {self.app_url}
        visited_urls = set()
        discovered_screens = {}

        while to_visit:
            url = to_visit.pop()
            if url in visited_urls:
                continue

            print(f"  -> Crawling: {url}")
            driver.get(url)
            time.sleep(2)  # Wait for single-page app to render

            body_text = driver.find_element(By.TAG_NAME, "body").text
            content_hash = hashlib.md5(body_text.encode()).hexdigest()
            screen_id = f"screen_{content_hash}"
            
            if screen_id not in discovered_screens:
                screenshot_path = f"output/{screen_id}.png"
                driver.save_screenshot(screenshot_path)
                
                discovered_screens[screen_id] = {
                    'screen_id': screen_id,
                    'url': url,
                    'title': driver.title,
                    'image_path': screenshot_path,
                }
                visited_urls.add(url)

                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute('href')
                    # Ensure href is an absolute URL before adding
                    if href and href.startswith("http") and href.startswith(self.app_url) and href not in visited_urls:
                        to_visit.add(href)
        
        driver.quit()
        print(f"✅ Crawler finished. Discovered {len(discovered_screens)} unique screens.")
        return list(discovered_screens.values())

    async def generate_ai_descriptions(self, screens: list):
        """Generates AI descriptions for each discovered screen."""
        print("\n🧠 Generating AI descriptions for screens...")
        for screen in screens:
            print(f"  -> Analyzing: {screen['url']}")
            try:
                prompt = f"""
                Analyze this UI screenshot. Provide a concise, one-sentence description of its main purpose.
                Return a JSON object with a single key: "description".
                """
                image_part = {"mime_type": "image/png", "data": open(screen['image_path'], 'rb').read()}
                
                response = await self.llm.generate_content_async([prompt, image_part], 
                    generation_config={"response_mime_type": "application/json"})
                
                ai_data = json.loads(response.text)
                screen['description'] = ai_data.get('description', 'No description generated.')
                screen['screen_name'] = screen['title']
                
            except Exception as e:
                print(f"    -> Error analyzing screen: {e}")
                screen['description'] = "Error generating description."
                screen['screen_name'] = screen['title']
        
        print("✅ Descriptions generated.")
        return screens

    def build_vector_index(self, catalog_data: list):
        # ... (this method is unchanged)
        print("\n💾 Building and saving vector index...")
        descriptions = [item.get('description', '') for item in catalog_data]
        embeddings = self.embedding_model.encode(descriptions)
        vector_dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(vector_dimension)
        index = faiss.IndexIDMap(index)
        ids = np.array([i for i in range(len(catalog_data))])
        index.add_with_ids(embeddings.astype('float32'), ids)
        faiss.write_index(index, 'output/screens.index')
        print("✅ Vector index saved to 'output/screens.index'")

    async def run(self):
        """Executes the full catalog building pipeline."""
        if not os.path.exists('output'):
            os.makedirs('output')
            
        screens = self.crawl_app()
        screens_with_descriptions = await self.generate_ai_descriptions(screens)
        
        # Use the intelligent CodeMapper
        print("\n🗺️  Mapping URLs to source files...")
        for screen in screens_with_descriptions:
            source_file = self.code_mapper.find_source_file_for_url(screen['url'])
            # Normalize path separators for consistency
            screen['source_file'] = source_file.replace('\\', '/') if source_file else None
            print(f"  -> Mapped {screen['url']} to {screen['source_file']}")

        # Save the final catalog data
        with open('output/catalog.json', 'w') as f:
            json.dump(screens_with_descriptions, f, indent=2)
        print("\n✅ Catalog data saved to 'output/catalog.json'")

        self.build_vector_index(screens_with_descriptions)
        print("\n🎉 Catalog build complete!")


async def main():
    target_app_url = "https://saas-website-builder.vercel.app/"
    
    builder = CatalogBuilder(app_url=target_app_url, repo_path=config.REPO_PATH)
    await builder.run()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())