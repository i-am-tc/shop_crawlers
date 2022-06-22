from selenium.webdriver.common.by import By
from datetime import datetime
import helpers as hl


###################################################################################

# Params & Constants

MALL_URL = 'https://www.babylandbb.com/'
SHOP_NAME = 'babyland'
FEATHER_NAME = datetime.today().strftime('%Y%m%d') + SHOP_NAME +'.ft'

###################################################################################

def get_products(driver, catLink):

    products_data = []
    single_product_entry = {}
    product_count = 0

    # Go to proudct array page
    driver.get(catLink)

    # Get categories
    cats = [a.split('>')[1].split('<')[0] for a in driver.page_source.split('itemprop="name"')[2:]]
    if len(cats) == 0:
        print('no cats....')
        return products_data, product_count

    # Get all products
    eproducts = driver.find_elements(by=By.CLASS_NAME, value='js-product-miniature-wrapper')

    # Loop through each product, form up data entry for saving
    for ep in eproducts:
        single_product_entry['mallUrl'] = MALL_URL
        single_product_entry['cats'] = cats
        single_product_entry['catLink'] = catLink
        single_product_entry['productLabel'] = ep.find_element(by=By.CLASS_NAME, value='product-title').text
        single_product_entry['productDesc'] = ''
        single_product_entry['productUrl'] = ep.get_attribute('innerHTML').split('href="')[
            1].split('"')[0]
        single_product_entry['productImages'] = [a.get_attribute('innerHTML').split('src="')[1].split(
            '"')[0] for a in ep.find_elements(by=By.CLASS_NAME, value='thumbnail-container')]
        single_product_entry['productSpec'] = ''
        single_product_entry['productRating'] = ''
        # Convert price to float after scraping.
        productPrice = ep.find_element(by=By.CLASS_NAME, value='product-price').\
            text.replace('$', '').replace(',', '')
        if productPrice != '':
            single_product_entry['productPrice'] = float(productPrice)
        else:
            single_product_entry['productPrice'] = 0.0

        products_data.append(single_product_entry)
        product_count += 1

    return products_data, product_count


###################################################################################

if __name__ == '__main__':

    start = datetime.now()
    print('Time start: ', start)

    # Start driver. Persistently.
    driver = hl.start_driver_persist(MALL_URL, isSetWindow=True)

    # Get leaves
    elements = driver.find_elements(by=By.CLASS_NAME, value='cbp-category-link-w')

    leaves = []
    for element in elements:
        #element = elements[0]
        html = element.get_attribute('innerHTML')
        hrefs = html.split('href="')[1:]
        hrefs = [a.split('>')[0].split('"')[0] for a in hrefs]
        hrefs = list(set(hrefs))
        leaves.extend(hrefs)

    print('No of links to scrape:', len(leaves))

    link_count = 0
    index_progress = 0

    for catLink in leaves:

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