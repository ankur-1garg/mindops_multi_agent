import os
import json
from catalog_builder import CatalogBuilder


def crawl_only():
    """Run only the web crawler portion to capture application screens."""
    print("\n🕷️ Starting application crawler...")

    # Ensure output directory exists
    if not os.path.exists('output'):
        os.makedirs('output')
        print("Created output directory.")

    target_app_url = "https://saas-website-builder.vercel.app/"
    repo_path = os.getenv("REPO_PATH", "./local_repo")

    # Initialize the catalog builder but only use the crawler
    builder = CatalogBuilder(app_url=target_app_url, repo_path=repo_path)

    # Run the crawler and save screenshots
    screens = builder.crawl_app()

    # Save the basic screen information
    print(f"\n📸 Captured {len(screens)} unique screens.")
    print("Screenshots are saved in the output directory.")

    # Save screen data without AI descriptions
    with open('output/screens_basic.json', 'w') as f:
        json.dump(screens, f, indent=2)
    print("\n💾 Basic screen data saved to 'output/screens_basic.json'")


if __name__ == '__main__':
    crawl_only()
