from pywikiapi import *
import sys
import os



# Constants
FIRST_BUNDLE_INDEX = 2
LAST_BUNDLE_INDEX = 6
SECTION_STR = "=="
TABLE_START = "{|"
TABLE_END = "|}"
SLOT_IMAGE = "File:Bundle Slot.png"
ITEM_START = "{{"
ITEM_DELIM = "|"
ITEM_END = "}}"
ROW = "|-"
REDIRECT = "#REDIRECT"
LINK_START = "[["
LINK_END = "]]"



class Room:

	def __init__(self, name, bundles):
		self.name = name
		self.bundles = bundles

	def print_csv(self, file):
		for b in self.bundles:
			for i in b.item_counts:
				item_amount = b.item_counts[i]
				file.write(self.name + "," + b.name + ",," + str(b.num_needed) +
						   ",," + i.name + "," + str(item_amount) + "," +
						   str(int(i.spring)) + ","+str(int(i.summer)) +
						   "," + str(int(i.fall)) + "," +
						   str(int(i.winter)) + "," + i.description+"\n")

	def __str__(self):
		string = self.name + "\n"
		for b in self.bundles:
			string += str(b)
		return string



class Bundle:

	def __init__(self, name, num_needed, item_counts):
		self.name = name
		self.num_needed = num_needed
		self.item_counts = item_counts

	def __str__(self):
		string = self.name + ": " + str(self.num_needed) + "\n"
		for i in self.items:
			string += str(i) + "\n"
		return string



class Item:
	def __init__(self, name, spring, summer, fall, winter, description):
		self.name = name
		self.spring = spring
		self.summer = summer
		self.fall = fall
		self.winter = winter
		self.description = description



def get_rooms(wikitext, site):
	rooms = []
	for i in range(FIRST_BUNDLE_INDEX, LAST_BUNDLE_INDEX + 1):
		rooms.append(create_room(i, wikitext, site))
	return rooms
		


def create_room(num, wikitext, site):
	# Get section name
	str_index = 0
	for i in range(0, num - 1):
		for i in range(2):
			str_index = wikitext.index(SECTION_STR, str_index) + 2
	start_index = wikitext.index(SECTION_STR, str_index) + 2
	end_index = wikitext.index(SECTION_STR, start_index)
	
	section_name = wikitext[start_index:end_index]
	if print_flag: print("Creating Room: " + section_name)
	# Get section text
	section_end = wikitext.index(SECTION_STR, end_index + 2)
	section_text = wikitext[end_index+2:section_end]
	bundle_list = read_bundles(section_text, site)
	return Room(section_name, bundle_list)



def read_bundles(section_text, site):
	bundle_list = []
	table_index = -1
	while True:
		# Get table text
		try:
			table_index = section_text.index(TABLE_START, table_index + 1)
		except:
			break
		end_index = section_text.index(TABLE_END, table_index) + 2
		
		table_text = section_text[table_index:end_index]
		# Get table name
		try:
			id_index = table_text.index("id=") + 4
		except:
			continue
		id_end = table_text.index("\"", id_index)
		id_text = table_text[id_index:id_end]
		if print_flag: print("Creating Bundle: " + id_text)
		# Get number of slots
		num_slots = table_text.count(SLOT_IMAGE)
		# Get items
		item_dict = read_items(table_text, site)
		bundle_list.append(Bundle(id_text, num_slots, item_dict))
	return bundle_list



def read_items(table_text, site):
	item_dict = {}
	start_row = table_text.index(ROW)
	while True:
		try:
			end_row = table_text.index(ROW, start_row + 1)
			name_start = table_text.index(ITEM_START, start_row, end_row)
		except:
			break
		name_start = table_text.index(ITEM_DELIM, name_start, end_row) + 1
		name_end = table_text.index(ITEM_END, name_start, end_row)
		try:
			name_end = table_text.index(ITEM_DELIM, name_start, name_end)
			attribute_start = name_end + 1
			attribute_end = table_text.index(ITEM_END, attribute_start, end_row)
			# print(table_text[attribute_start-10:attribute_end])
		except:
			pass
		item_name = table_text[name_start:name_end]
		amount = 1
		try:
			amount = int(table_text[attribute_start:attribute_end])
			attribute_start=-1
			attribute_start=-1
		except:
			pass
		if print_flag: print("Creating item: " + item_name)
		item_dict[get_item_info(item_name, site)] = amount

		start_row = end_row
	return item_dict



def get_item_info(item_name, site):
	page_name = item_name
	while True:
		if print_flag: print("Querying: " + page_name)
		response = site(action="parse", page=page_name, prop=["wikitext"])
		wikitext = response["parse"]["wikitext"]
		if not wikitext.startswith(REDIRECT):
			break
		if print_flag: print(page_name + " " + wikitext)
		start_index = wikitext.index("[[") + 2
		end_index = wikitext.index("]]")
		page_name = wikitext[start_index:end_index]
	if download_files:
		fname = "wiki_pages\\" + item_name + ".txt"
		with open(fname, "w", encoding="utf-8") as f:
			f.write(wikitext)

	info_end = get_info_box_end(wikitext)
	spring = summer = fall = winter = False
	try:
		season_index = wikitext.index("season", 0, info_end)
		season_index = wikitext.index("=", season_index) + 2
		season_end = wikitext.index("\n", season_index)
		season_name = wikitext[season_index:season_end].lower()
		spring = season_name.find("spring") >= 0
		summer = season_name.find("summer") >= 0
		fall = season_name.find("fall") >= 0
		winter = season_name.find("winter") >= 0
	except:
		pass
	if ((not spring) and (not summer) and (not fall) and (not winter)):
		spring = summer = fall = winter = True
	description_start = wikitext.index("\n", info_end) + 1
	description_end = wikitext.index("\n", description_start)
	return Item(item_name, spring, summer, fall, winter, wikitext[description_start:description_end])



def get_info_box_end(wikitext):
	opening = -2
	closing = 0
	num_opened = 0
	num_closed = 0
	while (num_opened != num_closed or num_closed == 0):
		closing = wikitext.index("}}", closing + 2)
		num_closed += 1
		while True:
			try:
				opening = wikitext.index("{{", opening + 2, closing)
				num_opened += 1
			except:
				break
	return closing



def set_print_flag(bool_val):
	global print_flag
	print_flag = bool_val



def set_download_files(bool_val):
	global download_files
	download_files = bool_val



def get_site():
	return Site("https://stardewvalleywiki.com/mediawiki/api.php")



def main():
	set_print_flag(("-p") in sys.argv)
	set_download_files(("-f") in sys.argv)
	
	site = get_site()

	response = site(action="parse", page="Bundles", prop=["wikitext"])

	if print_flag: print("Querying Bundles")

	if not os.path.exists("wiki_pages"):
		os.makedirs("wiki_pages")

	# Uncomment to save xml to a file
	if download_files:
		fname = "wiki_pages\\Bundles.txt"
		with open(fname, "w", encoding="utf-8") as f:
			f.write(response["parse"]["wikitext"])

	room_list = get_rooms(response["parse"]["wikitext"], site)
	if print_flag: print("Generating csv...")
	stardew_csv = open("community_center.csv", "w")
	stardew_csv.write("Room,Bundle,Completed,Amount Needed,Have Item,Item,Amount,Spring,Summer,Fall,Winter,Description\n")
	for room in room_list:
		room.print_csv(stardew_csv)
	stardew_csv.close()

if __name__ == "__main__":
	main()
	print("Finished!")
