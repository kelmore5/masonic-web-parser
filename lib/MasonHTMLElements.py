class NationalPageElements:
    """
    XPath references to what is being searched for on Masonic's national page.
    Looking for region names and page links
    """

    page_link: str = 'http://masonicmaps.com/Home/How-to-Add-an-Organisation,-Province-or-District.aspx'
    regional_links: str = "//div[@id='centerEditable']"

    # Within regional_links
    regions: str = './/h4'
    links: str = './/a'


class RegionalPageElements:
    """
    XPath references to what needs to be parsed on Masonic's regional pages.
    Looking for organization name and page links
    """

    load_check: str = "//div[@class='npBox']"
    organization_links: str = "//div[contains(@class, 'text')]"
    page_not_found: str = "//strong[contains(.,'Page not found')]"
    system_error: str = "//span[contains(.,'System error')]"

    # Within organization_links
    name: str = './/a'
    address: str = ".//div[contains(.,'Address')]/../div[contains(@class, 'right')]//p"


class OrganizationPageElements:
    """
    XPath references to what needs to be parsed on Masonic's organization pages.
    Looking for the organization's name, address, founded date, meeting schedule,
    contact name, contact number, contact email, and website
    """

    load_check: str = "//div[@class='image1Box']"

    # Within load_check
    name: str = './/h2'
    # Parse out founded date - last text string; within load_check
    address: str = './/p'

    # Take the first one:
    meeting_schedule: str = "//span[@class='dateinstance']"

    contact_info: str = "//div[@class='address']"
    # Within contact_info - Outputs: [contact, phone, website, and email]]
    contact_info_items: str = ".//li"

    google_maps_link: str = "//a[@title='Click to see this area on Google Maps']"
    google_map_lat_idx: str = 'll='


class MasonHTMLElements(object):
    """
    This class hosts all the HTML elements that will be searched for within Masonic's web site
    via XPath
    """
    base_html: str = 'http://masonicmaps.com'

    national_elements: NationalPageElements = NationalPageElements()
    regional_elements: RegionalPageElements = RegionalPageElements()
    organization_elements: OrganizationPageElements = OrganizationPageElements()
