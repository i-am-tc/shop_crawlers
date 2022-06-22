from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import helpers as hl


###################################################################################

# Params & Constants

MALL_URL = 'https://www.bonjourhk.com/tc'
SHOP_NAME = 'bonjourhk'
SHOW_PROD_SLEEP_SECS = 4
FEATHER_NAME = datetime.today().strftime('%Y%m%d') + SHOP_NAME +'.ft'

###################################################################################


def get_level1_name(driver, search_for):
    """
    search_for: expects str, e.g: id of each level 1: category-menu-100 , category-menu-200 etc

    Takes id of each level 1 category-main-menu and find mandarin character name under menu
    """
    dropdowns = driver.find_element(by=By.ID, value='menu').find_elements(by=By.CLASS_NAME, value='dropdown')
    for item in dropdowns:
        if item.get_attribute('data-display') == '#' + search_for:
            return item.text


def get_level2_name(hyperlinks):
    """
    hyperlinks: expected to be a Selemium list of elements, HTML tag 'a'
    This list of hyperlink should be from a level 2, found by menu-col.
    """
    # Loop through each link
    for link in hyperlinks:

        # Check if it contains characters that are not names.
        # Assume that level 2 names does not contain > and ......

        if '<' not in link.get_attribute('innerHTML') and '......' not in link.get_attribute('innerHTML'):
            return link.get_attribute('textContent')


def all_links_and_cats_bonjourhk(driver):
    """
    Purpose: get all the links that we would like crawl.
    These links should lead us to a unique product array page which crawling then begins.
    Brand links may have some overlap with other links but that is acceptable.
    """

    # Both are list of lists
    all_urls = []
    all_cats = []

    # Level 1 categories.
    level1 = driver.find_elements(by=By.CLASS_NAME, value='category-main-menu')

    # Special Level 1: new arrivals , link not found anywhere else.
    new_arrival_url = driver.find_element(by=By.ID, value='menu').\
        find_element(by=By.CSS_SELECTOR, value='.dropdown.pop').find_element(by=By.TAG_NAME, value='a')
    all_urls.append(new_arrival_url.get_attribute('href'))
    all_cats.append([new_arrival_url.text])

    # For each level1 element
    for i in level1:

        # Get level 1 name for current category
        level1_name = get_level1_name(driver, i.get_attribute('id'))

        # Find all level2 in this level1 (i.e. all menu-col)
        # Find with wildcard. All level 2 categories in BonjourHK starts with menu-col sth sth
        # Source: https://is.gd/fhT2LN
        level2 = i.find_elements(by=By.CSS_SELECTOR, value="[class^='menu-col']")

        # For each level2 element (i.e. each menu-col)
        for j in level2:

            # Get all hyperlink elements within this level 2
            hyperlinks = j.find_elements(by=By.TAG_NAME, value='a')

            # Loop through each hyperlink element to find level 2 name
            # Only can be used for the case of menu-col having only 1 sub
            level2_name = get_level2_name(hyperlinks)

            # Check if sub even exist.
            # If no: only 2 levels deep. No level 3
            # 香薰香水: has a menu-col of its own, has no sub
            try:
                j.find_element(by=By.CLASS_NAME, value='sub').get_attribute('innerHTML')
                have_sub = True
            except NoSuchElementException:
                have_sub = False

            # If there is no sub, we know it has only 2 levels.
            if not have_sub:
                for link in hyperlinks:
                    all_urls.append(link.get_attribute('href'))
                    all_cats.append([level1_name, link.get_attribute('textContent')])

            if have_sub:

                # Level 2 categories in 生活百貨 is very inconsistent: that which should have its own menu-col apparently does not: e.g. 保險金融, 文具用品, 寵物用品 & 餐桌用品
                # Instead, we have multiple sub in a menu-col, the sub could only have '\n', could also have 1 or many level 3s in them
                # 生活百貨 also has a myriad of cases. Hence the complexity here.
                if len(j.find_elements(by=By.CLASS_NAME, value='sub')) > 1:

                    # For each sub
                    index = 0
                    for sub in j.find_elements(by=By.CLASS_NAME, value='sub'):

                        # Find how many 'a' tags there are
                        no_of_links_in_sub = len(sub.find_elements(by=By.TAG_NAME, value='a'))

                        # If there are no links in this sub, we know there are only 2 levels.
                        # DIY配件 category is like that.
                        if no_of_links_in_sub == 0:
                            all_urls.append(hyperlinks[index].get_attribute('href'))
                            all_cats.append([level1_name, hyperlinks[index].get_attribute('textContent')])
                            index += 1

                        # If there are links in this sub, then we know it 3 levels.
                        # We just need to be mindful of getting level 2 name in this case: increment an index by no_of_links_in_sub
                        else:
                            for link in sub.find_elements(by=By.TAG_NAME, value='a'):
                                all_urls.append(link.get_attribute('href'))
                                all_cats.append([level1_name, hyperlinks[index].get_attribute('textContent'), link.get_attribute('textContent')])
                            index += no_of_links_in_sub+1

                # Check if only 1 sub && it's only \n
                # If yes: only 2 levels deep. No level 3
                # DIY配件 & '母嬰護理' > '孕婦專區' : has a menu-col of its own, has only 1 sub with '\n'
                if j.find_element(by=By.CLASS_NAME, value='sub').get_attribute('innerHTML') == '\n' and len(j.find_elements(by=By.CLASS_NAME, value='sub')) == 1:
                    for link in hyperlinks:
                        all_urls.append(link.get_attribute('href'))
                        all_cats.append([level1_name, level2_name])

                # Check if only 1 sub && sub is not only \n
                # If so, we can be faily sure it has three levels.
                if j.find_element(by=By.CLASS_NAME, value='sub').get_attribute('innerHTML') != '\n' and len(j.find_elements(by=By.CLASS_NAME, value='sub')) == 1:
                    for link in hyperlinks:
                        if link.get_attribute('textContent') != '......':
                            level3_name = link.get_attribute('textContent')
                        else:
                            continue
                        if level2_name != level3_name:
                            all_urls.append(link.get_attribute('href'))
                            all_cats.append([level1_name, level2_name, level3_name])

    return all_urls , all_cats


def get_products(driver, catLink, categories):

    products_data = []
    single_product_entry = {}
    product_count = 0

    # Get all products
    try:
        products = WebDriverWait(driver, 3). \
            until(EC.presence_of_element_located((By.CLASS_NAME, 'product-list'))). \
            find_elements(by=By.CLASS_NAME, value='product-col')
    except TimeoutException:
        print('>>> No products on this page')
        return products_data , product_count

    # Loop through each product, form up data entry for saving
    for product in products:
        # Col 1
        single_product_entry['mallUrl'] = MALL_URL

        # Col 2
        single_product_entry['cats'] = categories

        # Col 3.
        single_product_entry['productUrl'] = \
            product.find_element(by=By.CLASS_NAME, value='caption'). \
            find_element(by=By.CLASS_NAME, value='item_name'). \
            find_element(by=By.TAG_NAME, value='a').\
            get_attribute('href')

        # Col 4
        single_product_entry['productLabel'] = \
            product.find_element(by=By.CLASS_NAME, value='caption').\
            find_element(by=By.CLASS_NAME, value='item_name').text

        # Col 5
        single_product_entry['productDesc'] = ''

        # Col 6. Fail gracefully if no price. Remove commas
        try:
            productPrice = product.find_element(by=By.CLASS_NAME, value='caption').\
                find_element(by=By.CLASS_NAME, value='price').\
                find_element(by=By.TAG_NAME, value='em').text
            while ',' in productPrice: productPrice = productPrice.replace(',', '')
            single_product_entry['productPrice'] = float(productPrice)
        except NoSuchElementException:
            print('>>> A product has no price in this page')
            single_product_entry['productPrice'] = 0.0

        # Col 7
        single_product_entry['productSpec'] = \
            product.find_element(by=By.CLASS_NAME, value='caption').\
            find_element(by=By.CLASS_NAME, value='item_unit').text

        # Col 8
        single_product_entry['productImages'] = \
            [product.find_element(by=By.CLASS_NAME, value='image').\
            find_element(by=By.TAG_NAME, value='img').\
            get_attribute('src')]

        # Col 9
        single_product_entry['productDetails'] = ''

        # Col 10
        single_product_entry['productRating'] = ''

        # Col 11
        try:
            product.find_element(by=By.CLASS_NAME, value='out_of_stock')
            single_product_entry['productStock'] = 0
        except NoSuchElementException:
            single_product_entry['productStock'] = 1

        # Col 12
        single_product_entry['catLink'] = catLink

        products_data.append(single_product_entry)
        product_count += 1

    return products_data , product_count


def get_page_urls(driver, link):
    """
    Because Bonjour's is a page mechanism for showing products, we need to get links to each page.
    At each link, we then collect product data because going to the next page.
    """

    try:
        # 1st page link to list
        page_urls = [link]

        # Get pagination element.
        pagination = driver.find_element(by=By.CLASS_NAME, value='pagination'). \
            find_elements(by=By.TAG_NAME, value='a')

        # Collect urls for page 2 and onwards
        for item in pagination[0:-2]:
            page_urls.append(item.get_attribute('href'))

    except NoSuchElementException:
        # If no such element, means we're only 1 page.
        # 1st page link to list
        page_urls = [link]

    return page_urls


###################################################################################


if __name__ == '__main__':

    start = datetime.now()
    print('Time start: ', start)

    # Start driver. Persistently.
    driver = hl.start_driver_persist(MALL_URL, isSetWindow=True)

###################################################################################

    # Get all product category listing page links from main page
    # We loop through this list of links and crawl accordingly.

    links_and_cats = all_links_and_cats_bonjourhk(driver)
    print('No of links to scrape:', len(links_and_cats[0]))

###################################################################################
    # Main crawl loop

    link_count = 0
    index_progress = 0

    for link in links_and_cats[0][index_progress:]:

        # Inits
        products = [] ; product_count = 0

        # Go to first page.
        driver.get(link)

        # Get categories hierarchy and number of categories
        categories = links_and_cats[1][index_progress]

        # Check if we have multiple pages and get link
        page_urls = get_page_urls(driver, link)

        # For each page
        for page in page_urls:

            # Go to page.
            driver.get(page)

            # Get all products
            max_tries = 3
            for i in range(0, max_tries):
                try:
                    products , product_count = get_products(driver, link, categories)
                    break
                except:
                    driver.quit()
                    driver = hl.start_driver(MALL_URL, isSetWindow=True)
                    driver.get(page)

        # Save to feather when we're done with each link & all of each link's products
        if products:
            print('>>> Saving feather file ...')
            hl.feather_it(products, 'data/' + FEATHER_NAME)
        else:
            print('>>> Not saving: empty products.')

        link_count += 1
        print('Link done:', link)
        print(datetime.now(), 'No. of links done:', link_count, 'No. of products:', product_count, 'Link index:', index_progress, '\n')
        index_progress += 1

    hl.bucket_it(local_path='C:/Users/sar02/Desktop/shop_crawlers/'+SHOP_NAME+'/data', bucketname='mystore', folder_key='shops/', feathername=FEATHER_NAME)
    print('Saved to S3 bucket')

    end = datetime.now()
    elapsed = end - start
    print('Time End:', end)
    print('Elapsed:', elapsed)