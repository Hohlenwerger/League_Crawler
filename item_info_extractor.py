
#

import selenium
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as waiter
from selenium.webdriver.support.expected_conditions import (
	visibility_of_element_located as visibility,
	element_to_be_clickable as clickable
)
import json
import io
import os
import time

def define_driver(download_path):
	# Define Download Path
	if not os.path.exists(download_path):
		os.mkdir(download_path)

	# Options
	options = ChromeOptions()
	options.add_experimental_option("excludeSwitches", ['enable-automation'])
	options.add_experimental_option(
		"prefs", {
			"download.default_directory": download_path,
			"download.prompt_for_download": False,
			"download.directory_upgrade": True,
			"profile.content_settings.exceptions.automatic_downloads.*.setting": 1
		}
	)

	return Chrome(executable_path='chromedriver.exe', options=options)

def get_items_names_urls(driver): 
	# Define Lol wiki champion section URL
	lolwiki_sctn_items_url = 'https://leagueoflegends.fandom.com/wiki/Item'

	# Open URL
	driver.get(lolwiki_sctn_items_url)

	# Wait for item-grid become visible and get it
	waiter(driver, 60).until(visibility((By.ID, 'item-grid')))
	item_grid = driver.find_element_by_id('item-grid')

	# Get Champions Page URL
	css_sel = 'a[class$="link-internal"]'
	waiter(driver, 60).until(visibility((By.CSS_SELECTOR, css_sel)))
	items_url = item_grid.find_elements_by_css_selector(css_sel)
	items_url = [i.get_attribute('href') for i in items_url]

	# Get Items' Names and Items' data-modes
	css_sel = 'div[class$="item-icon tooltips-init-complete"]'
	waiter(driver, 60). until(visibility((By.CSS_SELECTOR, css_sel)))
	itens_names = item_grid.find_elements_by_css_selector(css_sel)
	data_modes = [i.get_attribute('data-modes') for i in itens_names]
	data_search = [i.get_attribute('data-search') for i in itens_names]
	itens_names = [i.get_attribute('data-param') for i in itens_names]

	# Build an List of Tuples
	item_lst = list(zip(items_url, itens_names, data_modes, data_search))

	# Exclude data_modes without classic 5v5:

	# Define an limit for loop interactions based on the amout of chars in text
	item_lst_validate = len(item_lst)

	# Index
	i=0

	# While there's items to validate
	while item_lst_validate:
		# If the data_modes don't support "Classic 5v5"
		if item_lst[i][2].find("Classic 5v5") == -1:
			# Pop it
			item_lst.pop(i)

		# Otherwise, if item data_search contains the following champion names, pop it.
		# There some itens that are exclusive, none of those
		# (expect Viktor's, whose item is going to be removed, and Gangplank, whose is not really an item and will be inserted in simulator engine)
		# change the champion status
		elif item_lst[i][3].find("Kalista") != -1 or item_lst[i][3].find("Viktor") != -1 or item_lst[i][3].find("Gangplank") != -1 or item_lst[i][3].find("Pyke") != -1:
			item_lst.pop(i)
		# Otherwise
		else:
			# Increment index, check next item
			i+=1

		# Decrement the amout of items to validate
		item_lst_validate-=1

	# When some item is removed from the list,
	# the index of next item becomes the same index of the item you just removed.
	# That's why the variable "i" is not incremented when some item is removed.
	

	# Print if some item without "Classic 5v5" flag in it's data_modes ware aproved
	'''
	for x in item_lst:
		if x[2].find("Classic 5v5") == -1:
			print(x[2])
			print('\n')
	'''

	# Return an a Tuple Collection with Champions Names and URLs
	return item_lst


def get_status_in_item_text(keyword, item_status_text, category):
	# Build Keyword.
	# This format is an better way to find the value of status that we are searching for
	keyword = "|" + keyword + " ="

	# Store item_status_text length to check when the end of file has reached
	text_len = len(item_status_text)

	# If keyword exists on item's status' text
	if item_status_text.find(keyword) != -1:
		
		# Keep keyword's lenght
		keyword_length = len(keyword)	

		# Get index of the first char in keyword
		keyword_index = item_status_text.index(keyword)
		
		# Calc index of the next char after keyword
		string_crawler = keyword_index+keyword_length
		
		# Get the next char after keyword
		wanted_value = item_status_text[string_crawler]
		
		# Increment index counter
		string_crawler+=1

		#
		while "|" not in wanted_value and string_crawler < text_len:

			wanted_value = wanted_value + item_status_text[string_crawler]

			string_crawler+=1

		wanted_value = wanted_value.replace("|", "")

		# When category is Extra, it will always be an text, so, spaces must be preserved
		# Otherwise:
		if category != "Extra":
			wanted_value = wanted_value.replace(" ", "")
			return int(wanted_value.replace("}", ""))
		else: 
			return wanted_value

	# If keyword does not exists, return value 0
	else:
		return 0


def get_item_in_game_status(driver, item_name, item_url, items, dict_item_id):
	# Open URL
	driver.get(item_url)

	# Wait for mw-content-text become visible
	waiter(driver, 60).until(visibility((By.ID, 'mw-content-text')))
	# Find element by id
	item_context = driver.find_element_by_id('mw-content-text')

	css_sel = 'h2[class$="pi-item pi-item-spacing pi-title"]'
	waiter(driver, 60).until(visibility((By.CSS_SELECTOR, css_sel)))
	items_header = item_context.find_element_by_css_selector(css_sel)

	# Get Item's Status' Text URL
	css_sel = 'a[class$="external text"]'
	
	# Wait for anchor with URL
	waiter(driver, 60).until(visibility((By.CSS_SELECTOR, css_sel)))
	
	# Find anchor
	edit_item_url = items_header.find_element_by_css_selector(css_sel)
	
	# Get URL
	edit_item_url = edit_item_url.get_attribute('href')

	# Open URL
	driver.get(edit_item_url)

	# Wait for Textlong with item status
	waiter(driver, 60).until(visibility((By.ID, 'wpTextbox1')))
	
	# Get text
	item_status_text = driver.find_element_by_id('wpTextbox1').text

	# Convert all multiple spaces in single ones
	item_status_text = " ".join(item_status_text.split())

	# An Tuple with the name of status that can possible exists in text,
	# the name of status that should be append to items JSON,
	# and the catergory of status:
	# status: Should be add to items[id][status]
	# Primal: Should be add to items[id]
	# Extra: Should be add to items[id][Extra]. Extra is always an long string, so spaces must be preservated
	item_status_lt = [
		("tier","Tier","Primal"),
		("buy","Cost","Primal"),
		("sell","Sell","Primal"),
		("code", "Lolwiki item code","Primal"),
		("comb","Combination Cost","Primal"),
		("ad","Attack Damage","status"),
		("ap","Ability Power","status"),
		("as","Attack Speed","status"),
		("ms","Move Speed","status"),
		("mr","Magic Resist","status"),
		("armor","Armor","status"),
		("health","Health Points","status"),
		("mana","Mana","status"),
		("crit","Critical Strike Chance","status"),
		("cdr","Cooldown Reduction","status"),
		("cdrunique","Cooldown Reduction *Unique","status"),
		("hp5","Health Regeneration per 5 Secconds","status"),
		("mp5","Mana Regeneration per 5 Secconds","status"),
		("hsp","Heal and Shield Power","status"),
		("recipe","Item Recipe","Extra"),
		("builds","Can be upgraded into","Extra"),
		("pass","Passive Effect 1","Extra"),
		("pass2","Passive Effect 2","Extra"),
		("act","Active Effect","Extra"),
		("aura","Aura Effect","Extra"),
		("limit","Limitations","Extra")
	]
	
	# Define item id, an string with 4 chars.
	item_id = str(len(items)+1)
	while len(item_id) < 4:
		item_id = "0"+item_id

	# Define item json model, must be appended to items' dict after
	item_status_to_append = {
		item_id:{
			"ID": item_id,
			"Name": item_name,
			"Icon_Path": ""
		}
	} 

	# For each Tuple in item_status_lt(lt: List of Tuple)
	for keyword, status_name, category in item_status_lt:
		# Get status_value that is returned in function: get_status_in_item_text
		status_value = get_status_in_item_text(keyword, item_status_text, category)
		# If returned value is not 0
		if status_value:
			if category == "Primal":
				item_status_to_append[item_id][status_name] = status_value
			else:
				# Try to add status_value to item_status_to_append[item_id][category][status_name]
				# if status_name index has not been defined, throw an exception
				try:
					item_status_to_append[item_id][category][status_name] = status_value
				except:
					item_status_to_append[item_id][category] = {
						status_name: status_value
					}

	dict_item_id[item_name] = item_id
	#print(item_status_to_append[item_id])
	#print('\n')

	# Add item to items' dict
	items.append(item_status_to_append)

	#import pdb; pdb.set_trace()
	return


# Download Path
download_path = os.path.join(os.getcwd(), 'lol_item_data_collection')

# Define Driver
driver = define_driver(download_path)

# Get Champions Names and URLs
item_name_url_lst = get_items_names_urls(driver)

#print(item_name_url_lst)

items = []
dict_item_id = []

# For each found items
for url, name, game_modes, data_search in item_name_url_lst:
	get_item_in_game_status(driver, name, url, items, dict_item_id)

# TODO: Change "Item Recipe" and "Can be upgraded into" to show items' ids instead of names

'''
for item in items:
	if "Extra" in item:
		if "Can be upgraded into" in item["Extra"]:

		if "Item Recipe" in item["Extra"]	
		item_status_to_append[item_id][category][status_name] = status_value
'''
with open('items_json.txt', 'w') as outfile:
    json.dump(items, outfile)

import pdb; pdb.set_trace()
driver.quit()	