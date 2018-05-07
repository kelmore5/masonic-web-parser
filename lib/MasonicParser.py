import ast
import os.path
import sys
import time
from typing import List, Set, Union, Dict, Callable, TypeVar

# noinspection PyUnresolvedReferences
from MasonHTMLElements import MasonHTMLElements
# noinspection PyUnresolvedReferences
from SeleniumBrowser.lib.SeleniumBrowser import SeleniumBrowser
# noinspection PyUnresolvedReferences
from SeleniumBrowser.lib.XPathLookupProps import XPathLookupProps
# noinspection PyUnresolvedReferences
# from database.models.Keywords import Keywords, KeywordsKeys
# noinspection PyUnresolvedReferences
from database.models.RegionalLinks import RegionalLinks, RegionalLinksKeys
# noinspection PyUnresolvedReferences
from database.models.BaseModel import BaseModel
# noinspection PyUnresolvedReferences
from database.models.Organizations import Organizations, OrganizationsKeys

from peewee import *
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
# noinspection PyUnresolvedReferences,PyPep8Naming
from utils.lib.Arrays import Arrays as arrays
# noinspection PyUnresolvedReferences,PyPep8Naming
from utils.lib.Excel import Excel as sheets
# noinspection PyUnresolvedReferences,PyPep8Naming
from utils.lib.Jsons import Jsons as jsons

dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = os.path.abspath(os.path.join(dir_path, '..'))

sys.path.append(dir_path)

from lib.MasonHTMLElements import MasonHTMLElements
from lib.SeleniumBrowser.lib.SeleniumBrowser import SeleniumBrowser
from lib.SeleniumBrowser.lib.XPathLookupProps import XPathLookupProps
from lib.database.models.BaseModel import BaseModel
from lib.database.models.RegionalLinks import RegionalLinks
from lib.database.models.Organizations import Organizations, OrganizationsKeys

# from lib.database.models.Posts import Posts, PostsKeys
# from lib.database.models.Messages import Messages
# from lib.database.models.Keywords import Keywords

from lib.utils.lib.Jsons import Jsons as jsons

# Process: Get links from Top level > Get page link from second level > Get info from third level

# TODO: Get latitude/longitude somehow?
# Parse out information from individual organization pages
# Upload all to database
# Output to Excel

BaseModelT = TypeVar('T', bound=BaseModel)


class MasonicParser(object):
    """
    This class is a web crawler for MasonicMaps.com (http://masonicmaps.com/), which is a site
    that hosts information on charitable organizations throughout America, England, Ireland, and Scotland.

    The goal of this crawler is to search through Masonic's site, find all links to individual organizations
    on the site, and then parse each organization's web page for address and contact information.

    This is done by searching through three levels of pages on Masonic. The crawler starts at Masonic's
    list of nations here (http://masonicmaps.com/Home/How-to-Add-an-Organisation,-Province-or-District.aspx),
    visits each regional page (example here http://masonicmaps.com/Maps/Grand-Lodge-of-Scotland/PGL-Caithness.aspx),
    and then grabs the link to each charity's page from the region page. Once found, the crawler then goes
    to each individual organization's page and downloads its contact information. This includes name, address,
    founded date, meeting schedule, latitude, longitude, contact, contact email, contact phone number, and website.

    The crawler splits up this information into two databases: RegionalLink and Organizations (using SQLite).
    RegionalLinks stores each region's web page and Organizations stores each organization's web page and
    information parsed.

    To summarize, the crawler's search pattern is thus: National Page > Regional Page > Organization Page

    Once everything is said and done, the script will output an Excel file with all the information that
    was parsed from Masonic.

    * Note: This crawler relies on Selenium's browsing solution via Chrome/chromedriver and pyvirtualdisplay. Both
    must be installed for the script to work. Once done, a headless Selenium web browser will be created
    to allow the script to run in the background.

    * Note 2: The script utilizes SQLite for database storage as to be as transportable and self-contained as
    possible. However, it can be adapted to use other databases as the script relies on Peewee ORM for transactions.
    """

    db: SqliteDatabase
    browser: SeleniumBrowser
    search_elements: MasonHTMLElements

    # TODO: Check for chromedriver existence, exit if not
    def __init__(self, path_to_chromedriver: str = dir_path + "/lib/chromedriver"):
        """
        Initialize Selenium headless browser class, SQLite database, XPath search patterns for traversing
        Masonic, and create database tables

        :param path_to_chromedriver: The path to chromedriver which is used by Selenium for browsing via Chrome
        """
        self.browser = SeleniumBrowser(path_to_chromedriver)
        self.db = RegionalLinks.db
        self.db.connect()

        self.search_elements = MasonHTMLElements()
        self.db.create_tables([RegionalLinks, Organizations])

    def parse_masonic(self):
        """
        Parsing Masonic requires 3 steps:

        1) Parse the national page for regional page links
        2) Parse the regional pages for individual organization links
        3) Parse each organization web page for their information

        This script carries out those functions and then outputs all the extracted information to Excel

        :return:
        """
        # self.parse_national_page()

        # self.parse_region_pages()

        self.parse_organization_pages()

        # self.convert_database_for_output(RegionalLinks)

        self.browser.quit()

    def parse_national_page(self):
        """
        Browse to Masonic's organization page, parse all the groupings of links from the page,
        separate out chosen countries, parse each individual link per country,
        and then upload everytihng to a database

        Countries to be parsed: Ireland, Scotland, England

        Link being parsed: 'http://masonicmaps.com/Home/How-to-Add-an-Organisation,-Province-or-District.aspx'

        :return: void
        """
        elements = self.search_elements.national_elements
        link_view = elements.regional_links

        load_check: XPathLookupProps = XPathLookupProps(By.XPATH, link_view, done_message='Home page loaded')

        if not self.browser.browse_to_url(elements.page_link, load_check):
            self.browser.quit()
            raise SystemExit('Something went wrong when loading the home page, exiting script')

        # Parse html page and group links
        link_groupings: Dict[str, WebElement] = self.parse_regional_links_to_dict(self.browser.get_browser())

        # Upload link groups to database
        self.upload_regional_groupings_to_db(link_groupings)

    def parse_region_pages(self):
        """
        Uses Selenium browser and the parsed national page that should already be loaded into
        the database to parse each region page from Masonic.

        This function will take all the region links from the regional_links database,
        load them in Selenium, parse out each individual organization's name and link, and then
        upload the parsed data into the database

        :return: void
        """
        # Get HTML elements for region pages and set up Organizations object for uploading objects
        elements = self.search_elements.regional_elements
        orgs = Organizations()

        # Set up upload array, upload_count, and get regional links already downloaded and saved to database
        # Loop through each regional link, go to url, and parse out individual organization links
        # uploads: List[Organizations] = []
        upload_count = 0
        upload_step = 1
        # Check number 50
        temp_start = 156
        regional_links: List[RegionalLinks] = RegionalLinks.select().offset(temp_start)
        for idx in range(len(regional_links)):
            # Get regional link from db, go to url, parse orgs, add to uploads array
            # Upload to db every 100 uploads and restart browser every 500
            link = regional_links[idx]

            url = link.regional_link
            load_check: XPathLookupProps = XPathLookupProps(By.XPATH, elements.organization_links,
                                                            done_message='{} regional page loaded'.format(
                                                                link.regional_org))

            if not self.browser.browse_to_url(url, load_check):
                loaded_props: XPathLookupProps = XPathLookupProps(By.XPATH, elements.load_check, delay=10)
                not_found_props: XPathLookupProps = XPathLookupProps(By.XPATH, elements.page_not_found)
                system_error_props: XPathLookupProps = XPathLookupProps(By.XPATH, elements.system_error, delay=10)
                if self.browser.check_presence_of_element(loaded_props):
                    print('Page loaded, but no organization links found. Continuing')
                    continue
                elif self.browser.check_presence_of_element(system_error_props):
                    print('Page could not be loaded - System error. Continuing')
                    continue
                elif self.browser.check_presence_of_element(not_found_props):
                    print('Page could not be loaded - Does not exist. Continuing')
                    continue
                else:
                    self.browser.quit()
                    raise SystemExit('Something went wrong when loading the home page, exiting script')

            uploads = self.parse_organization_links_to_models(self.browser.get_browser(), link)
            upload_count += len(uploads)

            if upload_count > upload_step * 500:
                self.browser.restart_browser()
                upload_step += 1

    def parse_organization_pages(self):
        """
        Use Selenium browser and the pre-downloaded organization links (from parse_region_pages)
        to traverse each organization's web page and parse out the org's information.

        Information parsed: Name, Address, Founded Date, Meeting Schedule, Latitude, Longitude,
        and (if available) Contact, Contact Number, Contact Email, and Website

        This function uploads each organization as it is parsed and restarts Selenium browser
        every 100 orgs parsed to try and thwart bot protection

        prec: Selenium browser has been started
        postc: All organization information from Masonic will be uploaded to a database for export

        :return: void
        """
        # Re-instantiating Organizations to easily select keys
        OG = Organizations
        orgs = Organizations()

        # Get HTML elements and organization links from Organizations database
        elements = self.search_elements.organization_elements
        upload_count = 1
        org_links: List[Organizations] = Organizations.select(OG.national_org, OG.regional_org, OG.regional_link,
                                                              OG.name, OG.page_link)
        for idx in range(len(org_links)):
            org = org_links[idx]
            # Get url and create load check for browser
            url = org.page_link

            load_check: XPathLookupProps = XPathLookupProps(By.XPATH, elements.google_maps_link, delay=40,
                                                            done_message='{} organization page loaded'.format(org.name))

            # Browser to url for parsing
            if not self.browser.browse_to_url(url, load_check):
                print('Something went wrong when loading the organization page for {} at {}, exiting script'.format(
                    org.name, url))
                continue

            # Parse to model
            try:
                model = self.parse_organization_page_to_model(self.browser.get_browser(), org)
            except Exception as e:
                print(e)
                print('Something went wrong when parsing the organization page for {} at {}, exiting script'.format(
                    org.name, url))
                continue

            try:
                orgs.upload_many([model])
                upload_count += 1
            except Exception as e:
                print(model)
                print(e)
                continue

            if upload_count % 20 == 0:
                print('Uploaded {} records so far'.format(str(upload_count)))

            if upload_count % 100 == 0:
                self.browser.restart_browser()
                time.sleep(60)

            if upload_count % 1000 == 0:
                time.sleep(60 * 10)

    def parse_organization_page_to_model(self, html_tree: webdriver.Chrome, model: Organizations) -> Organizations:
        """
        Once an organization's web page is loaded, parse its information into a database model
        to be uploaded.

        Looking for: Name, Address, Founded Date, Meeting Schedule, Contact Name, Contact Number, Contact Email,
        and Website

        prec: WebDriver has been loaded with the page's link
        postc: Returns a database model for the Organization being parsed

        :param html_tree: Selenium web browser loaded with the page's link
        :param model: The Organizations model (which should already be in the database from parsing the regional link)
        :return: The Organization model, but filled in with data from the parsed page
        """

        # Get HTML elements to search for
        elements = self.search_elements.organization_elements

        # Get main info - name, number, address, and founded date here
        main_info: WebElement = html_tree.find_element_by_xpath(elements.load_check)

        # Parse out organization name and number
        name = main_info.find_element_by_xpath(elements.name).text
        number_idx = name.rfind('No.')

        number = name[(number_idx + 3):].strip()
        name = name[:number_idx].strip()

        # Parse out organization address and founded date
        address_element: WebElement = main_info.find_element_by_xpath(elements.address)
        address_parse: List[str] = address_element.get_attribute('innerHTML').split('<br>')
        founded_check: str = address_parse.pop()

        # Make sure founded date is present before adding to model
        founded: str = None
        if 'Founded' in founded_check:
            founded = founded_check[(founded_check.index(' ') + 1):]
        else:
            address_parse.append(founded_check)

        address = '\n'.join(address_parse)

        # Parse out meeting schedule - easy
        meeting_schedule: str = html_tree.find_element_by_xpath(elements.meeting_schedule).text

        # Parse out contact info - contact, phone, website, and email found here
        contact_info_element: WebElement = html_tree.find_element_by_xpath(elements.contact_info)
        contact_info: List[WebElement] = contact_info_element.find_elements_by_xpath(elements.contact_info_items)

        # Parse out contact, phone, website, email from inside ul/li elements
        contact = contact_info[0].text
        phone = contact_info[1].text
        website = contact_info[2].text
        email = contact_info[3].text

        check_map: XPathLookupProps = XPathLookupProps(By.XPATH, elements.google_maps_link)
        latitude: str = None
        longitude: str = None
        if self.browser.check_presence_of_element(check_map):
            google_maps_a_tag: WebElement = html_tree.find_element_by_xpath(elements.google_maps_link)
            google_maps_link: str = google_maps_a_tag.get_attribute('href')

            latitude = google_maps_link[(google_maps_link.index(elements.google_map_lat_idx) + 3):]
            latitude = latitude[:latitude.index(',')]

            longitude = google_maps_link[(google_maps_link.index(elements.google_map_lat_idx) + 3):]
            longitude = longitude[(longitude.index(',') + 1):longitude.index('&z=')]

        # Finally, update model attributes
        model.name = name
        model.number = number
        model.address = address
        model.founded_date = founded

        if model.founded_date == '':
            model.founded_date = None

        model.meeting_schedule = meeting_schedule

        # Check if contact information is there before updating
        contact_check = 'sign up'
        if contact_check not in contact:
            model.contact = contact[(contact.index(':') + 1):].strip()
        if contact_check not in phone:
            model.phone = phone[(phone.index(':') + 1):].strip()
        if contact_check not in website:
            model.website = website[(website.index('site') + 4):].strip()
        if contact_check not in email:
            model.email = email[(email.index(':') + 1):].strip()

        model.latitude = float(latitude) if latitude is not None else None
        model.longitude = float(longitude) if longitude is not None else None

        # Return filled in model
        return model

    def parse_organization_links_to_models(self, html_tree: webdriver.Chrome, regional_model: RegionalLinks) -> \
            List[Organizations]:
        """
        This function parses out each individual organization's link from the region page on Masonic.
        First, it gets all the organizations' html elements, then it parses out their name, building number,
        address, and page_link. Afterwards, the page_links will be used to get the rest of the information
        for each org

        prec: html_tree has been loaded with the region's url
        postc: returns Organizations to be uploaded

        :param html_tree: A Selenium browser that has already been loaded with the region's url
        :param regional_model: The base regional_model from where the region's url came from. Used to fill
            in new model's national_org, regional_org, and regional_link for db foreign keys
        :return: A list of Organizations to upload to the database
        """
        # Get HTML elements for regional page
        elements = self.search_elements.regional_elements
        org_service = Organizations()

        # Split up region page into each individual org and create upload array
        # Loop through elements and parse out individual page links
        # Each element = new Organization to upload to database
        org_uploads: List[Organizations] = []
        upload_count = 0
        upload_step = 1
        orgs = html_tree.find_elements_by_xpath(elements.organization_links)
        for idx in range(len(orgs)):
            org = orgs[idx]

            # Get primary key properties from region, set up new model
            region = regional_model.to_dict()
            region.pop(RegionalLinksKeys.created_at, None)

            model = Organizations.initialize(region)

            # Get organization name, parse out name, address, and number
            org_name_html = org.find_element_by_xpath(elements.name)

            # Takes a long time
            org_address = org.find_element_by_xpath(elements.address)
            org_name = org_name_html.get_attribute('text')

            # Parse out number by splitting up title of organization
            parse_org = org_name.split(' ')
            org_number = parse_org.pop()
            org_name = ' '.join(parse_org)

            # Set model properties and add to upload array
            # Takes a long time
            model.page_link = org_name_html.get_attribute('href')
            model.name = org_name
            model.number = org_number
            model.address = org_address.get_attribute('innerHTML').replace('<br>', '\n').strip()

            if model.number == '':
                model.number = -1

            address_len = len(model.address)
            if model.address.rfind(',') + 1 == address_len:
                model.address = model.address[:(address_len - 1)].strip()

            org_uploads.append(model)

            if len(org_uploads) >= 100 or idx + 1 == len(orgs):
                org_service.upload_many(org_uploads)
                upload_count += len(org_uploads)
                print('Uploaded {} records, {} total'.format(str(len(org_uploads)), str(upload_count)))
                org_uploads.clear()

        # Return upload array
        return org_uploads

    def parse_regional_links_to_dict(self, html_tree: webdriver.Chrome) -> Dict[str, WebElement]:
        """
        After browsing to Masonic's organization home page, parse through
        the home page and group each section of links by the countries being parsed.
        Returns a dictionary of said groupings

        Countries being searched: England, Ireland, Scotland

        :param html_tree: Selenium browser already loaded and ready to be parsed
        :return: A dictionary where keys = countries being searched
            and values = the WebElement grouping of links
        """
        # Get HTML elements to search for
        elements = self.search_elements.national_elements
        link_elements = elements.regions

        # Grab data for these countries
        search_params = ['England', 'Ireland', 'Scotland']

        # Separate out links and convert to text for searching
        web_links: List[WebElement] = html_tree.find_elements_by_xpath(link_elements)[1:]
        regional_names: List[str] = [x.text.strip() for x in web_links]

        # Loop through headers and search for text containing search_params above
        # If found, add index to links_to_grab
        links_to_grab: Set[int] = set()
        for org_idx in range(len(regional_names)):
            header = regional_names[org_idx]

            for search in search_params:
                if search in header:
                    links_to_grab.add(org_idx)

        # Loop through links_to_grab (should be about 6)
        # Add index of WebElement from web_links to link_groupings dictionary,
        # using the country as the key
        link_groupings: dict = dict()
        for idx in links_to_grab:
            link_groupings[regional_names[idx]] = web_links[idx + 1]

        # Outputs dictionary with key -> country, value -> WebElement containing all links for country
        return link_groupings

    def upload_regional_groupings_to_db(self, link_groupings: Dict[str, WebElement]):
        """
        After Masonic's organization links are parsed out, loop through all the groupings,
        parse out each individual link, and upload everything to a database for future parsing

        :param link_groupings: Dictionary of WebElements grouped by country
            key = district, values = WebElements
        :return: void
        """
        # Get HTML elements to search for
        elements = self.search_elements.national_elements

        # Loop through link_groupings/page of WebElements and parse into DistrictLinks models
        countries: List[str] = link_groupings.keys()
        district_db_upload: List[RegionalLinks] = []
        for country in countries:
            # Get elements and links
            html_elements = link_groupings[country]
            links = html_elements.find_elements_by_xpath(elements.links)

            # Loop through all links and parse into models
            for element in links:
                # Get name and link
                regional_org = element.text
                link = element.get_attribute('href')

                # Create model dictionary/model
                district_dict = {'national_org': country, 'regional_org': regional_org, 'regional_link': link}
                district = RegionalLinks.initialize(district_dict)

                # Add to uploads
                district_db_upload.append(district)

        # Upload to db
        RegionalLinks().upload_many(district_db_upload)

    # TODO: Move to utils class
    @staticmethod
    def convert_database_for_output(db: BaseModelT):
        keys: List[str] = db._meta.get_sorted_fields()
        rows: List[BaseModel] = db.select()

        remove_keys = ['created_at', 'id']
        for key in remove_keys:
            keys.remove(key) if key in keys else 0

        convert_header: Callable[[str], str] = lambda x: x.replace('_', ' ').title()
        new_keys: List[str] = [convert_header(x) for x in keys]
        new_rows: List[dict] = [x.to_dict() for x in rows]

        output: List[List[str]] = [new_keys, []]
        for row in new_rows:
            new_row: List[str] = []

            for key in keys:
                if key in row:
                    new_row.append(row[key])
                else:
                    new_row.append('')

        return output

    @staticmethod
    def output_keywords_to_excel():
        # TODO: Format excel spreadsheet output
        sheet_rows = []
        # headers = ["Title", "Page Link", "Keyword Group", "Keywords Found in Title", "Keywords Found in Messages",
        #            "Post Creation Date", "Post Last Response Date"]
        #
        # output: List[Union[Keywords, Posts]] = Keywords.select(Keywords.title, Keywords.link, Keywords.group,
        #                                                        Keywords.keywords_in_title, Keywords.keywords_in_message,
        #                                                        Posts.creation_date.alias("creation_date"),
        #                                                        Posts.last_post_date) \
        #     .join(Posts, JOIN.LEFT_OUTER, on=(Posts.link == Keywords.link)).order_by(Keywords.group.desc())
        #
        # rem_brackets = lambda x: x.replace('[', '').replace(']', '').replace('\'', '')
        #
        # sheet_rows.append(headers)
        # sheet_rows.append([""] * 7)
        # for keyword in output:
        #     # noinspection PyUnresolvedReferences
        #     new_row = [keyword.title.title, keyword.link.link, keyword.group, rem_brackets(keyword.keywords_in_title),
        #                rem_brackets(keyword.keywords_in_message), keyword.posts.creation_date,
        #                keyword.posts.last_post_date]
        #     sheet_rows.append(new_row)
        #
        # sheet_rows += [[]] + [["Total Keywords"]] + [[]]
        # sheet_rows += [["Positive Keywords:"]] + [[]] + keyword_rows[0] + [[]]
        # sheet_rows += [["Negative Keywords:"]] + [[]] + keyword_rows[1]
        #
        # output_path = os.path.dirname(os.path.realpath(__file__))
        # output_path = os.path.abspath(os.path.join(output_path, '../output/output.xlsx'))
        #
        # sheets.create_master_sheet(output_path, sheet_rows)


# TODO: Catch KeyboardInterrupt and close browser - super big memory leaks if opened/exited a lot
parser = MasonicParser()
parser.parse_masonic()
