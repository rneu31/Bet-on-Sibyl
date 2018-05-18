from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup


def selenium_get_page_content(url):
    print('Scraping with selenium ...')
    soup = None
    options = Options()
    options.set_headless(headless=True)
    driver = webdriver.Firefox(firefox_options=options)

    try:
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        # Quit in a finally block to ensure the quit happens even
        # in scenarios where an exception occurs.
        driver.quit()

    return soup
