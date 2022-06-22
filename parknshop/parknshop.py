from selenium.common.exceptions import NoSuchElementException, WebDriverException, \
    ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import helpers as hl


###################################################################################

# Params & Constants

MALL_URL = 'https://www.parknshop.com/zh-hk/'
SHOP_NAME = 'parknshop'
SHOW_PROD_SLEEP_SECS = 3.5
FEATHER_NAME = datetime.today().strftime('%Y%m%d') + SHOP_NAME +'.ft'

###################################################################################

def all_links_parknshop(driver):
    """
    Purpose: get all the links that we would like crawled.
    These links should lead us to a unique product array page which crawling then begins.
    Brand links may have some overlap with other links but that is acceptable.
    """

    output = []

    # Level 1 categories that is visually only 1 level deep
    no_sub_cat = driver.find_element(by=By.CSS_SELECTOR, value='.lv2-container.sub-category.pns-revamp-font-icons').\
        find_elements(by=By.CLASS_NAME, value='lv2-no-subcategory')

    for link in no_sub_cat:
        url = link.get_attribute('href')
        output.append(url)

    # Level 1 categories that is visually organized to 2 levels deep
    sub_cat = driver.find_element(by=By.CSS_SELECTOR, value='.lv2-container.sub-category.pns-revamp-font-icons').\
        find_elements(by=By.CLASS_NAME, value='lv2-subcategory')

    for i in sub_cat:
        sub_cat_urls = i.find_element(by=By.ID, value='m-subcategory-').find_elements(by=By.TAG_NAME, value='a')
        for url in sub_cat_urls:
            output.append(url.get_attribute('href'))

    # Level 1 categories with a special brand categories
    brands_cat = driver.find_element(by=By.CSS_SELECTOR, value='.lv2-container.sub-category.pns-revamp-font-icons').\
        find_elements(by=By.CLASS_NAME, value='brands')

    for i in brands_cat:
        brand_cat_urls = i.find_elements(by=By.TAG_NAME, value='a')
        for url in brand_cat_urls:
            output.append(url.get_attribute('href'))

    # Remove duplicates and pickle it.
    # with open('all_links_parknshop.pickle', 'wb') as f:
    #     pickle.dump(list(set(output)), f)

    return output


def get_products(driver, catLink):

    products_data = []
    single_product_entry = {}
    product_count = 0

    # Go to a product-category's page. We expect an array of products to be displayed
    driver.get(MALL_URL + link)

    # Get categories hierarchy and number of categories
    categories = WebDriverWait(driver, 10). \
        until(EC.presence_of_element_located((By.ID, 'breadcrumb'))). \
        text
    categories = categories.split('>')[1:]

    # Click through all show product buttons. This is a time bottleneck.
    while True:
        try:
            show_all_product = driver.find_element(by=By.PARTIAL_LINK_TEXT, value='顯示更多')
            show_all_product.click()
            time.sleep(SHOW_PROD_SLEEP_SECS)
        except NoSuchElementException or StaleElementReferenceException or ElementClickInterceptedException:
            break

    # Get all products
    products = WebDriverWait(driver, 10). \
        until(EC.presence_of_element_located((By.ID, 'product-list'))). \
        find_element(by=By.CLASS_NAME, value='product-container'). \
        find_elements(by=By.CLASS_NAME, value='padding')

    # Loop through each product, form up data entry for saving
    for product in products:
        # Col 1
        single_product_entry['mallUrl'] = MALL_URL

        # Col 2
        single_product_entry['cats'] = categories

        # Col 3
        single_product_entry['productUrl'] = product.find_element(by=By.CLASS_NAME, value='ClickSearchResultEvent_Class').get_attribute('href')

        # Col 4
        single_product_entry['productLabel'] = product.find_element(by=By.CLASS_NAME, value='name').text

        # Col 5
        single_product_entry['productDesc'] = ''

        # Col 6
        while True:
            try:
                productPrice = product.find_element(by=By.CSS_SELECTOR, value='.price.discount.newPrice').text[3:]
                # Check and remove any number of commas from price
                while ',' in productPrice: productPrice = productPrice.replace(',', '')
                single_product_entry['productPrice'] = float(productPrice)
                break
            except NoSuchElementException:
                print('1st method to get price failed. Going for 2nd ...')

            try:
                productPrice = product.find_element(by=By.CSS_SELECTOR, value='.price.discount.mbPrice').text[3:]
                # Check and remove any  number of commas from price
                while ',' in productPrice: productPrice = productPrice.replace(',', '')
                single_product_entry['productPrice'] = float(productPrice)
                break
            except NoSuchElementException:
                print('>>> A product has no price in this page')
                single_product_entry['productPrice'] = 0.0
                break

        # Col 7
        single_product_entry['productSpec'] = product.find_element(by=By.CLASS_NAME, value='volumn').text

        # Col 8
        single_product_entry['productImages'] = [product.find_element(by=By.TAG_NAME, value='img').get_attribute('src')]

        # Col 9
        single_product_entry['productDetails'] = ''

        # Col 10
        single_product_entry['productRating'] = ''

        # Col 11
        try:
            product.find_element(by=By.ID, value='product-icon-topSeller')
            single_product_entry['topSeller'] = 1
        except:
            single_product_entry['topSeller'] = 0

        # Col 12
        try:
            product.find_element(by=By.ID, value='product-icon-new')
            single_product_entry['newProduct'] = 1
        except:
            single_product_entry['newProduct'] = 0

        # Col 13
        try:
            product.find_element(by=By.CSS_SELECTOR,
                                 value='.tool-tips.tips-mouseover.tips-no-fullscreen.product-non-country-icon.eShopOnly')
            single_product_entry['eShopOnly'] = 1
        except:
            single_product_entry['eShopOnly'] = 0

        # Col 14
        try:
            product.find_element(by=By.ID, value='product-icon-organic')
            single_product_entry['organic'] = 1
        except:
            single_product_entry['organic'] = 0

        # Col 15
        try:
            product.find_element(by=By.ID, value='product-icon-soyaFree')
            single_product_entry['soyaFree'] = 1
        except:
            single_product_entry['soyaFree'] = 0

        # Col 16
        try:
            product.find_element(by=By.ID, value='product-icon-healthyFat')
            single_product_entry['healthyFat'] = 1
        except:
            single_product_entry['healthyFat'] = 0

        # Col 17
        try:
            product.find_element(by=By.CSS_SELECTOR, value='.button.cartButton.notifyMe')
            single_product_entry['productStock'] = 0
        except NoSuchElementException:
            single_product_entry['productStock'] = 1

        # Col 18
        single_product_entry['catLink'] = catLink

        # Append each products_data dict together
        products_data.append(single_product_entry)
        product_count += 1

    return products_data , product_count

###################################################################################


if __name__ == '__main__':

    start = datetime.now()
    print('Time Start: ', start)

    # Start driver. Persistently.
    driver = hl.start_driver_persist(MALL_URL, isSetWindow=True)

###################################################################################

    # Get all product category listing page links from main page
    # We loop through this list of links and crawl accordingly.

    links = all_links_parknshop(driver)
    print('No of links to scrape:', len(links))

###################################################################################
    # Main crawl loop

    link_count = 0
    index_progress = 0

    for link in links[index_progress:]:

        # Inits
        products = [] ; product_count = 0

        # Get product
        max_tries = 3
        for i in range(0,max_tries):
            try:
                products , product_count = get_products(driver, link)
                break
            except:
                driver.quit()
                driver = hl.start_driver(MALL_URL, isSetWindow=True)

        # Save to feather when we're done with each link & all of each link's products
        if products:
            print('>>> Saving feather file ...')
            hl.feather_it(products, 'data/' + FEATHER_NAME)
        else:
            print('>>> Not saving: empty products.')

        link_count += 1
        print('Link done:', link)
        print(datetime.now(), 'No. of links done:', link_count, 'No. of products:', product_count, 'Link index:', index_progress ,'\n')
        index_progress += 1

    hl.bucket_it(local_path='C:/Users/sar02/Desktop/shop_crawlers/'+SHOP_NAME+'/data', bucketname='mystore', folder_key='shops/', feathername=FEATHER_NAME)
    print('Saved to S3 bucket')

    end = datetime.now()
    elapsed = end - start
    print('Time End:', end)
    print('Elapsed:', elapsed)