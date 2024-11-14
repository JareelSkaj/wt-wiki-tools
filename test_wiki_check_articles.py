import unittest
from unittest.mock import patch
import io
from wiki_check_articles import check_sections, process_category_page, get_links_to_analyze, analyze_pages

# run with: python -m unittest test_wiki_check_articles.py
class TestWikiCheckArticles(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_check_sections_valid_article(self, mock_stdout):
        url = "https://wiki.warthunder.com/IJN_Kongo"
        title, found_sections, missing_sections = check_sections(url)
        self.assertEqual(title, "IJN Kongo")
        self.assertIn("Description", found_sections)
        self.assertIn("Survivability and armour", found_sections)
        self.assertIn("Mobility", found_sections)
        self.assertIn("Primary armament", found_sections)
        self.assertIn("Secondary armament", found_sections)
        self.assertIn("Anti-aircraft armament", found_sections)
        self.assertIn("Usage in battles", found_sections)
        self.assertIn("Pros and cons", found_sections)
        self.assertIn("History", found_sections)
        self.assertNotIn("Additional armament", found_sections)
        self.assertNotIn("Additional armament", missing_sections)
        self.assertGreater(len(found_sections), 9)

        url = "https://wiki.warthunder.com/index.php?title=B7A2_(Homare_23)&oldid=194625"
        title, found_sections, missing_sections = check_sections(url)
        self.assertEqual(title, "B7A2 (Homare 23)")
        self.assertIn("Description", found_sections)
        self.assertIn("Survivability and armour", found_sections)
        self.assertIn("Offensive armament", found_sections)
        self.assertIn("Suspended armament", found_sections)
        self.assertIn("Defensive armament", found_sections)
        self.assertIn("Usage in battles", found_sections)
        self.assertIn("Pros and cons", found_sections)
        self.assertIn("History", missing_sections)
        self.assertNotIn("Description", missing_sections)
        self.assertNotIn("Survivability and armour", missing_sections)
        self.assertNotIn("Offensive armament", missing_sections)
        self.assertNotIn("Suspended armament", missing_sections)
        self.assertNotIn("Defensive armament", missing_sections)
        self.assertNotIn("Usage in battles", missing_sections)
        self.assertNotIn("Pros and cons", missing_sections)
        self.assertNotIn("History", found_sections)
        # Check for the sections that are not present in the article
        # see if they are correctly excluded from both lists
        self.assertNotIn("Mobility", found_sections)
        self.assertNotIn("Mobility", missing_sections)
        self.assertNotIn("Primary armament", found_sections)
        self.assertNotIn("Primary armament", missing_sections)
        self.assertNotIn("Main armament", found_sections)
        self.assertNotIn("Main armament", missing_sections)
        self.assertNotIn("Secondary armament", found_sections)
        self.assertNotIn("Secondary armament", missing_sections)
        self.assertNotIn("Anti-aircraft armament", found_sections)
        self.assertNotIn("Anti-aircraft armament", missing_sections)
        self.assertNotIn("Additional armament", found_sections)
        self.assertNotIn("Additional armament", missing_sections)
        self.assertNotIn("Scout plane", found_sections) 
        self.assertNotIn("Scout plane", missing_sections)

        # this article can have "Usage in battles" incorrectly listed as a found section if something is wrong in check_sections
        # the opposite of this page is https://wiki.warthunder.com/index.php?title=Poltava&oldid=177683
        url = "https://wiki.warthunder.com/index.php?title=Marat&oldid=191173"
        title, found_sections, missing_sections = check_sections(url)
        self.assertEqual(title, "Marat")
        self.assertIn("Description", missing_sections)
        self.assertIn("Survivability and armour", missing_sections)
        self.assertIn("Primary armament", missing_sections)
        self.assertIn("Secondary armament", missing_sections)
        self.assertIn("Anti-aircraft armament", missing_sections)
        self.assertIn("Additional armament", missing_sections)
        self.assertIn("Usage in battles", missing_sections)
        self.assertIn("Pros and cons", missing_sections)
        self.assertIn("History", missing_sections)
        self.assertNotIn("Description", found_sections)
        self.assertNotIn("Survivability and armour", found_sections)
        self.assertNotIn("Primary armament", found_sections)
        self.assertNotIn("Secondary armament", found_sections)
        self.assertNotIn("Anti-aircraft armament", found_sections)
        self.assertNotIn("Additional armament", found_sections)
        self.assertNotIn("Usage in battles", found_sections)
        self.assertNotIn("Pros and cons", found_sections)
        self.assertNotIn("History", found_sections)
        
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_check_sections_invalid_article(self, mock_stdout):
        url = "https://wiki.warthunder.com/Invalid_Article"
        result = check_sections(url)
        self.assertIsNone(result[0])
  
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_process_category_page(self, mock_stdout):
        # Category with no articles, but a tech tree preview that should be ignored
        url = "https://wiki.warthunder.com/Category:Coastal_Fleet_USA"
        links = process_category_page(url)
        self.assertEqual(len(links), 0)

        # this category uses a select with ".mw-content-ltr li"
        url = "https://wiki.warthunder.com/Category:UCAV"
        links = process_category_page(url)
        self.assertGreaterEqual(len(links), 3)

        url = "https://wiki.warthunder.com/Category:Cruisers"
        # Test with 'n' subcategories response
        with patch('builtins.input', return_value='n'):
            links = process_category_page(url)
            self.assertEqual(len(links), 2) # only the links to subcategories

        url = "https://wiki.warthunder.com/Category:Light_cruisers"
        count_light_cruisers = len(process_category_page(url))
        self.assertGreater(count_light_cruisers, 0)
        url = "https://wiki.warthunder.com/Category:Heavy_cruisers"
        count_heavy_cruisers = len(process_category_page(url))
        self.assertGreater(count_heavy_cruisers, 0)
        
        # check if scrapping subcategories is working correctly
        url = "https://wiki.warthunder.com/Category:Cruisers"
        # Test with 'y' subcategories response
        with patch('builtins.input', return_value='y'):
            links = process_category_page(url)
            self.assertEqual(len(links), 2 + count_light_cruisers + count_heavy_cruisers)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_get_links_single_article(self, mock_stdout):
        url = "https://wiki.warthunder.com/IJN_Kongo"
        links = get_links_to_analyze(url)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0], url)
        
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_get_links_category(self, mock_stdout):
        url = "https://wiki.warthunder.com/Category:Sixth_rank_ships"
        links = get_links_to_analyze(url)
        self.assertGreater(len(links), 0)


if __name__ == '__main__':
    unittest.main()
