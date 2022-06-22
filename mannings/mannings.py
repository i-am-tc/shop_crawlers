from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
import helpers as hl


###################################################################################

# Params & Constants

MALL_URL = 'https://www.mannings.com.hk/'
SHOP_NAME = 'mannings'
FEATHER_NAME = datetime.today().strftime('%Y%m%d') + SHOP_NAME +'.ft'

###################################################################################

def get_products(driver, catLink):

    products_data = []
    single_product_entry = {}
    product_count = 0

    # Go to proudct array page
    driver.get(catLink)

    # Get categories
    ecats = driver.find_elements(by=By.CLASS_NAME, value='breadcrumb-item')
    if len(ecats) == 0:
        return products_data, product_count
    cats = [a.text for a in ecats[1:]]

    # Get all products
    eproducts = driver.find_elements(by=By.CLASS_NAME, value='product_content')

    # Loop through each product, form up data entry for saving
    for ep in eproducts:

        single_product_entry['mallUrl'] = MALL_URL
        single_product_entry['cats'] = cats
        single_product_entry['catLink'] = catLink
        single_product_entry['productLabel'] = ep.find_element(by=By.CLASS_NAME, value='product_name').text
        single_product_entry['productDesc'] = ''
        single_product_entry['productUrl'] = ep.find_element(by=By.CLASS_NAME, value='product_name').get_attribute('href')
        single_product_entry['productImages'] = [a.get_attribute(
            'href') for a in ep.find_elements(by=By.CLASS_NAME, value='product-image')]
        single_product_entry['productSpec'] = ''
        single_product_entry['productRating'] = ''
        try:
            productPrice = ep.find_element(by=By.CLASS_NAME, value='offered_price').text.replace('$', '').replace(',', '')
        except:
            productPrice = ep.find_element(by=By.CLASS_NAME, value='product_price').text.replace('$', '').replace(',', '')
        # print('productPrice', 'content:', productPrice, 'len:',
        #       len(productPrice), 'type', type(productPrice),
        #       'have whitespace?:', ' ' in productPrice == True,
        #       'have newline?:', '\n' in productPrice == True,
        #       'have empty space?:', '' in productPrice == True)
        if len(productPrice) != 0:
            single_product_entry['productPrice'] = float(productPrice)
        else:
            single_product_entry['productPrice'] = 0.0

        products_data.append(single_product_entry)
        product_count += 1

    return products_data, product_count


def switch_language(driver):

    # Find element containing hyperlink
    lang_btn = driver.find_element(by=By.ID, value='lang-form').\
        find_element(by=By.LINK_TEXT, value='繁中')

    try:
        # Try to click it in case stupid pop up advert goes away.
        lang_btn.click()
    except:
        # Click 5 pixels down and 5 pixels right of lang_btn
        # Then click lang_btn.
        # Wait 1 seconds for things to load.
        # Source: https://is.gd/1HWWfV
        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(lang_btn, 5, 5)
        action.click()
        action.perform()
        lang_btn.click()
    return driver


###################################################################################

if __name__ == '__main__':

    start = datetime.now()
    print('Time start: ', start)

    # Start driver. Persistently.
    driver = hl.start_driver_persist(MALL_URL, isSetWindow=True)

    # Switch language
    driver = switch_language(driver)

    # Get leaves, aka links that brings us to each product's category>subcategory page
    elements = driver.find_elements(by=By.CLASS_NAME, value='yCmsComponent')
    leaves = []
    for element in elements:
        html = element.get_attribute('innerHTML')
        hrefs = html.split('href="')
        hrefs = [a.split('>')[0].split('"')[0] for a in hrefs if 'title' in a]
        hrefs = list(set(hrefs))
        leaves.extend(hrefs)
    leaves = [a for a in leaves if 'mannings.com' not in a]

    links = [MALL_URL + a for a in leaves]
    print('No of links to scrape:', len(links))

    link_count = 0
    index_progress = 0

    for catLink in links:

        # Inits
        products = [] ; product_count = 0

        # Get all products
        max_tries = 3
        for i in range(0, max_tries):
            try:
                products, product_count = get_products(driver, catLink)
                break
            except:
                driver.quit()
                driver = hl.start_driver(MALL_URL, isSetWindow=True)
                driver = switch_language(driver)

        # Save to feather when we're done with each link & all of each link's products
        if products:
            print('>>> Saving feather file ...')
            hl.feather_it(products, 'data/' + FEATHER_NAME)
        else:
            print('>>> Not saving: empty products.')

        link_count += 1
        print('Link done:', catLink)
        print(datetime.now(), 'No. of links done:', link_count, 'No. of products:', product_count, 'Link index:', index_progress, '\n')
        index_progress += 1

    hl.bucket_it(local_path='C:/Users/sar02/Desktop/shop_crawlers/'+SHOP_NAME+'/data', bucketname='mystore', folder_key='shops/', feathername=FEATHER_NAME)
    print('Saved to S3 bucket')

    end = datetime.now()
    elapsed = end - start
    print('Time End:', end)
    print('Elapsed:', elapsed)